#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from local.arithmetic import solve_arithmetic
from local.code import solve_code
from local.logic import solve_logic
from local.ner import solve_ner
from local.qwen import call_qwen_audit, call_qwen_batch
from local.repair import repair_answer
from local.sentiment import solve_sentiment
from local.summary import solve_summary
from local.validation import infer_category, task_prompt, validate_answer
INPUT_PATH = Path(os.getenv('INPUT_PATH', '/input/tasks.json'))
OUTPUT_PATH = Path(os.getenv('OUTPUT_PATH', '/output/results.json'))
START_TIME = time.monotonic()
TOTAL_BUDGET_SECONDS = int(os.getenv('ROUTEIQ_TOTAL_BUDGET_SECONDS', '575'))

def seconds_left() -> float:
    return TOTAL_BUDGET_SECONDS - (time.monotonic() - START_TIME)

def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)

def load_tasks() -> list[dict[str, Any]]:
    with INPUT_PATH.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if isinstance(data, list):
        tasks = data
    elif isinstance(data, dict) and isinstance(data.get('tasks'), list):
        tasks = data['tasks']
    else:
        raise ValueError('tasks.json must be a list or contain a tasks list')
    normalized: list[dict[str, Any]] = []
    for index, raw_task in enumerate(tasks):
        if not isinstance(raw_task, dict):
            raise ValueError(f'Task {index} is not an object')
        task = dict(raw_task)
        if 'task_id' not in task:
            if 'id' in task:
                task['task_id'] = task['id']
            else:
                raise ValueError(f'Task {index} has no task_id')
        normalized.append(task)
    return normalized

def write_results(results: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(results, handle, ensure_ascii=False, separators=(',', ':'))
    temporary.replace(OUTPUT_PATH)

def parse_allowed_models() -> list[str]:
    raw = os.getenv('ALLOWED_MODELS', '').strip()
    if not raw:
        raise ValueError('ALLOWED_MODELS is missing')
    try:
        decoded = json.loads(raw)
        if isinstance(decoded, list):
            models = [str(item).strip() for item in decoded if str(item).strip()]
            if models:
                return models
    except json.JSONDecodeError:
        pass
    pieces = raw.replace(';', ',').replace('\n', ',').split(',') if ',' in raw else raw.split()
    models = [item.strip() for item in pieces if item.strip()]
    if not models:
        raise ValueError('ALLOWED_MODELS has no usable models')
    return models

def ordered_models(models: list[str]) -> list[str]:
    ordered: list[str] = []
    for keyword in ('minimax', 'gemma', 'kimi'):
        for model in models:
            if keyword in model.lower() and model not in ordered:
                ordered.append(model)
    for model in models:
        if model not in ordered:
            ordered.append(model)
    return ordered

def completion_url() -> str:
    base = os.getenv('FIREWORKS_BASE_URL', '').strip().rstrip('/')
    if not base:
        raise ValueError('FIREWORKS_BASE_URL is missing')
    return base if base.endswith('/chat/completions') else f'{base}/chat/completions'

def model_candidates(model: str, url: str) -> list[str]:
    value = model.strip()
    candidates = [value]
    if 'api.fireworks.ai' in url.lower() and (not value.startswith('accounts/')) and ('/' not in value):
        candidates.append(f'accounts/fireworks/models/{value}')
    return candidates

def compact_tasks(tasks: list[dict[str, Any]]) -> str:
    payload = [{'i': str(task['task_id']), 'p': task_prompt(task)} for task in tasks]
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))

def extract_json(content: str) -> Any:
    cleaned = content.strip()
    if cleaned.startswith('```'):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip().startswith('```'):
            lines = lines[:-1]
        cleaned = '\n'.join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    object_start, object_end = (cleaned.find('{'), cleaned.rfind('}'))
    if object_start != -1 and object_end > object_start:
        try:
            return json.loads(cleaned[object_start:object_end + 1])
        except json.JSONDecodeError:
            pass
    array_start, array_end = (cleaned.find('['), cleaned.rfind(']'))
    if array_start != -1 and array_end > array_start:
        return json.loads(cleaned[array_start:array_end + 1])
    raise ValueError('Model response did not contain valid JSON')

def normalize_answer(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

def parse_batch_results(content: str, tasks: list[dict[str, Any]]) -> dict[str, str]:
    decoded = extract_json(content)
    if isinstance(decoded, dict):
        for key in ('r', 'results', 'answers', 'data'):
            if isinstance(decoded.get(key), list):
                decoded = decoded[key]
                break
    if not isinstance(decoded, list):
        raise ValueError('Batch response is not a result list')
    expected_ids = [str(task['task_id']) for task in tasks]
    expected_set = set(expected_ids)
    results: dict[str, str] = {}
    for index, item in enumerate(decoded):
        if not isinstance(item, dict):
            continue
        task_id = item.get('i', item.get('task_id', item.get('id')))
        if task_id is None and index < len(expected_ids):
            task_id = expected_ids[index]
        task_id = str(task_id).strip() if task_id is not None else ''
        if task_id not in expected_set or task_id in results:
            continue
        answer = item.get('a', item.get('answer', item.get('output', item.get('response'))))
        normalized = normalize_answer(answer)
        if normalized:
            results[task_id] = normalized
    return results

def batch_response_format() -> dict[str, Any]:
    return {'type': 'json_schema', 'json_schema': {'name': 'R', 'schema': {'type': 'object', 'properties': {'r': {'type': 'array', 'items': {'type': 'object', 'properties': {'i': {'anyOf': [{'type': 'string'}, {'type': 'integer'}]}, 'a': {'type': 'string'}}, 'required': ['i', 'a'], 'additionalProperties': False}}}, 'required': ['r'], 'additionalProperties': False}}}

def _perform_request(payload: dict[str, Any], api_key: str, url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), method='POST', headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json', 'Accept': 'application/json'})
    remaining = seconds_left() - 10
    if remaining <= 5:
        raise TimeoutError('RouteIQ runtime budget exhausted before remote request')
    with urllib.request.urlopen(request, timeout=max(5, min(120, int(remaining)))) as response:
        return json.loads(response.read().decode('utf-8'))

def request_batch(tasks: list[dict[str, Any]], model: str, api_key: str, url: str) -> dict[str, str]:
    payload = {'model': model, 'messages': [{'role': 'system', 'content': 'Solve accurately. Obey exact requested format. Return JSON {"r":[{"i":"task id","a":"answer"}]}; include every task once. No reasoning unless requested; code must be complete.'}, {'role': 'user', 'content': compact_tasks(tasks)}], 'temperature': 0, 'max_tokens': min(4096, max(256, 220 * len(tasks))), 'stream': False, 'response_format': batch_response_format()}
    try:
        body = _perform_request(payload, api_key, url)
    except urllib.error.HTTPError as error:
        details = error.read().decode('utf-8', errors='replace')
        if error.code not in (400, 422):
            raise RuntimeError(f'Fireworks HTTP {error.code}: {details[:500]}') from error
        log('Structured output rejected; retrying plain JSON')
        fallback_payload = dict(payload)
        fallback_payload.pop('response_format', None)
        body = _perform_request(fallback_payload, api_key, url)
    choices = body.get('choices', [])
    if not choices:
        raise RuntimeError('Fireworks response contains no choices')
    content = choices[0].get('message', {}).get('content')
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError('Fireworks response contains no answer text')
    answers = parse_batch_results(content, tasks)
    if not answers:
        raise RuntimeError('Remote response contained no usable answers')
    return answers

def call_batch(tasks: list[dict[str, Any]], models: list[str], api_key: str, url: str) -> dict[str, str]:
    last_error: Exception | None = None
    for model in ordered_models(models):
        for candidate in model_candidates(model, url):
            try:
                log(f'Attempting one remote batch with: {candidate}')
                answers = request_batch(tasks, candidate, api_key, url)
                if answers:
                    return answers
            except Exception as error:
                last_error = error
                log(f'Remote model {candidate} failed: {type(error).__name__}: {error}')
    raise last_error or RuntimeError('All batch models failed')

def call_missing_individually(missing: list[dict[str, Any]], models: list[str], api_key: str, url: str) -> dict[str, str]:
    recovered: dict[str, str] = {}
    for task in missing:
        if seconds_left() < 35:
            log('Stopping individual recovery to preserve the container runtime budget')
            break
        task_id = str(task['task_id'])
        try:
            answer_map = call_batch([task], models, api_key, url)
            answer = answer_map.get(task_id, '')
            valid, reason = validate_answer(task, answer)
            if valid:
                recovered[task_id] = answer
            else:
                log(f'Remote validation rejected {task_id}: {reason}')
        except Exception as error:
            log(f'Fallback task {task_id} failed: {type(error).__name__}: {error}')
    return recovered

def resolve_local_tasks(tasks: list[dict[str, Any]]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    answers: dict[str, str] = {}
    unresolved: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task['task_id'])
        text = task_prompt(task)
        if not text:
            unresolved.append(task)
            log(f'Local reject {task_id}: no unambiguous task text')
            continue
        decisions = (('arithmetic', solve_arithmetic(text)), ('sentiment', solve_sentiment(task)), ('logic', solve_logic(text)), ('ner', solve_ner(text)), ('code', solve_code(task)), ('summary', solve_summary(task)))
        accepted = False
        reasons: list[str] = []
        for specialist, decision in decisions:
            reasons.append(f'{specialist}={decision.reason}')
            if not decision.accepted or not decision.answer:
                continue
            valid, validation_reason = validate_answer(task, decision.answer)
            if not valid:
                reasons.append(f'{specialist}_validation={validation_reason}')
                continue
            answers[task_id] = decision.answer
            log(f'Local {specialist} accept {task_id}: {decision.reason}')
            accepted = True
            break
        if not accepted:
            unresolved.append(task)
            log(f'Local reject {task_id}: {'; '.join(reasons)}')
    return (answers, unresolved)

def _validated_subset(tasks: list[dict[str, Any]], proposed: dict[str, str], source: str) -> dict[str, str]:
    task_by_id = {str(task['task_id']): task for task in tasks}
    accepted: dict[str, str] = {}
    for task_id, answer in proposed.items():
        task = task_by_id.get(str(task_id))
        if not task:
            continue
        repaired = repair_answer(task, answer)
        valid, reason = validate_answer(task, repaired)
        if valid:
            accepted[str(task_id)] = repaired
        else:
            log(f'{source} validation rejected {task_id}: {reason}')
    return accepted

def call_qwen_microbatches(tasks: list[dict[str, Any]]) -> dict[str, str]:
    """Run no more than three task-family batches through local Qwen.

    This isolates knowledge/extraction, reasoning/code, and language tasks
    while avoiding one giant mixed prompt. It remains fully local.
    """
    if not tasks:
        return {}
    families: dict[str, list[dict[str, Any]]] = {'knowledge': [], 'reasoning': [], 'language': []}
    for task in tasks:
        category = infer_category(task)
        if category in {'factual', 'ner'}:
            families['knowledge'].append(task)
        elif category in {'logic', 'math', 'code'}:
            families['reasoning'].append(task)
        else:
            families['language'].append(task)
    answers: dict[str, str] = {}
    minimum_remaining = int(os.getenv('QWEN_MICROBATCH_MIN_REMAINING', '65'))
    for family in ('knowledge', 'reasoning', 'language'):
        batch = families[family]
        if not batch:
            continue
        if seconds_left() < minimum_remaining:
            log(f'Skipping Qwen {family} microbatch: only {seconds_left():.1f}s remain')
            continue
        try:
            log(f'Running Qwen {family} microbatch with {len(batch)} tasks')
            proposed = call_qwen_batch(batch)
            for task_id, answer in proposed.items():
                if task_id not in answers and answer:
                    answers[task_id] = answer
        except Exception as error:
            log(f'Qwen {family} microbatch failed: {type(error).__name__}: {error}')
    return answers

def main() -> int:
    try:
        tasks = load_tasks()
    except Exception as error:
        log(f'Input error: {error}')
        write_results([])
        return 1
    local_answers, unresolved = resolve_local_tasks(tasks)
    answers = dict(local_answers)
    qwen_answers: dict[str, str] = {}
    if unresolved:
        try:
            log(f'Attempting local Qwen proposal batch for {len(unresolved)} tasks')
            raw_qwen = call_qwen_microbatches(unresolved)
            qwen_answers = _validated_subset(unresolved, raw_qwen, 'Qwen proposal')
            answers.update(qwen_answers)
            log(f'Qwen proposal accepted {len(qwen_answers)} of {len(raw_qwen)} recovered answers')
        except Exception as error:
            log(f'Local Qwen proposal failed: {type(error).__name__}: {error}')
        audit_enabled = os.getenv('QWEN_AUDIT_ENABLED', '0').strip() == '1'
        audit_candidates = [task for task in unresolved if infer_category(task) == 'factual' or not answers.get(str(task['task_id']), '').strip()]
        if audit_enabled and audit_candidates and (seconds_left() >= 85):
            try:
                log(f'Auditing {len(audit_candidates)} high-risk local answers')
                drafts = {str(task['task_id']): answers.get(str(task['task_id']), '') for task in audit_candidates}
                raw_audit = call_qwen_audit(audit_candidates, drafts)
                audited = _validated_subset(audit_candidates, raw_audit, 'Qwen audit')
                answers.update(audited)
                qwen_answers.update(audited)
                log(f'Qwen audit accepted {len(audited)} of {len(raw_audit)} recovered answers')
            except Exception as error:
                log(f'Local Qwen audit failed; retaining valid proposals: {type(error).__name__}: {error}')
    remote_candidates = [task for task in unresolved if not answers.get(str(task['task_id']), '').strip()]
    log(f'Routing summary: deterministic={len(local_answers)}; qwen={len(qwen_answers)}; remote={len(remote_candidates)}')
    local_only = True
    if remote_candidates and (not local_only):
        try:
            models = parse_allowed_models()
            url = completion_url()
            api_key = os.getenv('FIREWORKS_API_KEY', '').strip()
            if not api_key:
                raise ValueError('FIREWORKS_API_KEY is missing')
        except Exception as error:
            log(f'Remote configuration error: {error}')
            models, url, api_key = ([], '', '')
        if models and url and api_key and (seconds_left() >= 25):
            try:
                raw_remote = call_batch(remote_candidates, models, api_key, url)
                remote_answers = _validated_subset(remote_candidates, raw_remote, 'Remote')
                answers.update(remote_answers)
            except Exception as error:
                log(f'Primary remote batch failed: {type(error).__name__}: {error}')
            missing = [task for task in remote_candidates if not answers.get(str(task['task_id']), '').strip()]
            if missing:
                log(f'Recovering {len(missing)} missing remote answers individually')
                answers.update(call_missing_individually(missing, models, api_key, url))
    elif local_only and remote_candidates:
        log(f'Local-only benchmark: leaving {len(remote_candidates)} tasks unresolved')
    results = [{'task_id': task['task_id'], 'answer': answers.get(str(task['task_id']), '')} for task in tasks]
    write_results(results)
    completed = sum((1 for result in results if result['answer']))
    log(f'Wrote {len(results)} results; completed={completed}; missing={len(results) - completed}; deterministic={len(local_answers)}; qwen={len(qwen_answers)}; remote_needed={len(remote_candidates)}')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
