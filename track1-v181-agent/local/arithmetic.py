from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Callable


@dataclass(frozen=True)
class LocalDecision:
    accepted: bool
    answer: str = ""
    reason: str = ""


MAX_ABSOLUTE_VALUE = Fraction(10**15)
MAX_EXPONENT = 10
NUMBER_PATTERN = r"[-+]?\d+(?:\.\d+)?"
FRACTION_PATTERN = r"(?:\d+\s*/\s*\d+|\d+(?:\.\d+)?)"


def _reject(reason: str) -> LocalDecision:
    return LocalDecision(False, reason=reason)


def _accept(value: Fraction, reason: str) -> LocalDecision:
    return LocalDecision(True, _format_fraction(value), reason)


def _accept_text(answer: str, reason: str) -> LocalDecision:
    return LocalDecision(True, answer.strip(), reason)


def _guard(value: Fraction) -> Fraction:
    if abs(value) > MAX_ABSOLUTE_VALUE:
        raise ValueError("result exceeds safe magnitude")
    if value.denominator > 10**12:
        raise ValueError("denominator exceeds safe limit")
    return value


def _constant_to_fraction(value: object) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("unsupported constant")
    return _guard(Fraction(str(value)))


def _evaluate_node(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body)
    if isinstance(node, ast.Constant):
        return _constant_to_fraction(node.value)
    if isinstance(node, ast.UnaryOp):
        operand = _evaluate_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return _guard(-operand)
        raise ValueError("unsupported unary operator")
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        operation: Callable[[Fraction, Fraction], Fraction]
        if isinstance(node.op, ast.Add):
            operation = lambda a, b: a + b
        elif isinstance(node.op, ast.Sub):
            operation = lambda a, b: a - b
        elif isinstance(node.op, ast.Mult):
            operation = lambda a, b: a * b
        elif isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("division by zero")
            operation = lambda a, b: a / b
        elif isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ValueError("division by zero")
            operation = lambda a, b: Fraction(a // b)
        elif isinstance(node.op, ast.Mod):
            if right == 0:
                raise ValueError("modulo by zero")
            operation = lambda a, b: a % b
        elif isinstance(node.op, ast.Pow):
            if right.denominator != 1:
                raise ValueError("fractional exponent rejected")
            exponent = right.numerator
            if abs(exponent) > MAX_EXPONENT:
                raise ValueError("exponent exceeds safe limit")
            if left == 0 and exponent < 0:
                raise ValueError("zero cannot have negative exponent")
            operation = lambda a, b: a ** int(b)
        else:
            raise ValueError("unsupported binary operator")
        return _guard(operation(left, right))
    raise ValueError(f"unsupported syntax: {type(node).__name__}")


def _safe_evaluate(expression: str) -> Fraction:
    if len(expression) > 200:
        raise ValueError("expression too long")
    if "^" in expression:
        raise ValueError("caret exponent syntax is ambiguous")
    return _evaluate_node(ast.parse(expression, mode="eval"))


def _has_finite_decimal(denominator: int) -> bool:
    remaining = denominator
    for factor in (2, 5):
        while remaining % factor == 0:
            remaining //= factor
    return remaining == 1


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if _has_finite_decimal(value.denominator):
        with localcontext() as context:
            context.prec = 30
            decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        formatted = format(decimal_value, "f").rstrip("0").rstrip(".")
        return formatted or "0"
    return format(float(value), ".12g")


def _normalise(text: str) -> str:
    replacements = {
        "×": "*", "÷": "/", "−": "-", "–": "-", "—": "-",
        "₹": "", "$": "", "€": "", "£": "", ",": "",
    }
    normalised = text.strip().lower()
    for old, new in replacements.items():
        normalised = normalised.replace(old, new)
    return re.sub(r"\s+", " ", normalised).strip()


def _extract_numbers(text: str) -> list[Fraction]:
    return [Fraction(value) for value in re.findall(NUMBER_PATTERN, text)]


def _parse_fraction(value: str) -> Fraction:
    value = re.sub(r"\s+", "", value)
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        denominator_value = int(denominator)
        if denominator_value == 0:
            raise ValueError("division by zero")
        return Fraction(int(numerator), denominator_value)
    return Fraction(value)


def _solve_percentage_of(text: str) -> LocalDecision | None:
    match = re.fullmatch(
        rf"(?:what is |calculate |compute )?({NUMBER_PATTERN})\s*%\s+of\s+({NUMBER_PATTERN})\??",
        text,
    )
    if not match:
        return None
    return _accept(
        _guard(Fraction(match.group(2)) * Fraction(match.group(1)) / 100),
        "exact percentage-of pattern",
    )


def _solve_chained_discount_tax(text: str) -> LocalDecision | None:
    if not ("discount" in text and ("tax" in text or "gst" in text) and ("then" in text or "after" in text)):
        return None
    numbers = _extract_numbers(text)
    if len(numbers) != 3:
        return _reject("discount-tax pattern did not contain exactly three numbers")
    base, discount, tax = numbers
    if base < 0 or not (0 <= discount <= 100 and 0 <= tax <= 100):
        return _reject("unsafe discount-tax values")
    final_value = base * (1 - discount / 100) * (1 + tax / 100)
    return _accept(_guard(final_value), "exact chained discount-tax pattern")


def _solve_single_percentage_change(text: str) -> LocalDecision | None:
    increase = any(word in text for word in ("increase", "increased", "add", "markup"))
    decrease = any(word in text for word in ("decrease", "decreased", "discount", "discounted", "reduce", "reduced"))
    if increase == decrease or "%" not in text:
        return None
    numbers = _extract_numbers(text)
    if len(numbers) != 2:
        return _reject("percentage-change pattern did not contain exactly two numbers")
    base, percentage = numbers
    if base < 0 or not 0 <= percentage <= 100:
        return _reject("unsafe percentage-change values")
    multiplier = 1 + percentage / 100 if increase else 1 - percentage / 100
    return _accept(_guard(base * multiplier), "exact single percentage-change pattern")


def _solve_inventory_sequence(text: str) -> LocalDecision | None:
    if not any(word in text for word in ("warehouse", "store", "stock", "inventory", "units", "items")):
        return None
    base_match = re.search(
        rf"(?:starts?|begins?|has|had)\s+(?:with\s+)?({NUMBER_PATTERN})\s+(?:units|items|products|pieces|boxes|widgets)",
        text,
    )
    if not base_match:
        return None
    value = Fraction(base_match.group(1))
    events: list[tuple[int, str, Fraction]] = []
    for match in re.finditer(rf"(?:sells?|sold)\s+({NUMBER_PATTERN})\s*%", text):
        events.append((match.start(), "percent_sale", Fraction(match.group(1))))
    for match in re.finditer(
        rf"(?:restocks?|restocked|receives?|received|adds?|added|replenishes?|replenished)\s+(?:with\s+)?({NUMBER_PATTERN})\s*(?:units|items|products|pieces|boxes|widgets)?",
        text,
    ):
        events.append((match.start(), "add", Fraction(match.group(1))))
    for match in re.finditer(
        rf"(?:sells?|sold|ships?|shipped)\s+({NUMBER_PATTERN})\s+(?:more\s+)?(?:units|items|products|pieces|boxes|widgets)",
        text,
    ):
        if "%" not in match.group(0):
            events.append((match.start(), "subtract", Fraction(match.group(1))))
    for match in re.finditer(
        rf"\band\s+({NUMBER_PATTERN})\s+more\b",
        text,
    ):
        events.append((match.start(), "subtract", Fraction(match.group(1))))
    if not events:
        return None
    events.sort(key=lambda item: item[0])
    for _, kind, amount in events:
        if kind == "percent_sale":
            if not 0 <= amount <= 100:
                return _reject("inventory percentage outside safe range")
            value -= value * amount / 100
        elif kind == "add":
            value += amount
        else:
            value -= amount
        _guard(value)
    if value < 0:
        return _reject("inventory result became negative")
    return _accept(_guard(value), "ordered inventory word-problem pattern")


def _solve_recipe_scaling(text: str) -> LocalDecision | None:
    if not any(word in text for word in ("recipe", "cookies", "servings", "people", "cakes")):
        return None
    quantity_match = re.search(
        rf"requires?\s+({FRACTION_PATTERN})\s+(cup|cups|tablespoon|tablespoons|teaspoon|teaspoons|kg|g|litre|litres|liter|liters)\s+of\s+.+?\s+for\s+({NUMBER_PATTERN})\s+([a-z]+)",
        text,
    )
    target_match = re.search(rf"(?:needed|required)\s+for\s+({NUMBER_PATTERN})\s+([a-z]+)", text)
    if not quantity_match or not target_match:
        return None
    try:
        base_quantity = _parse_fraction(quantity_match.group(1))
    except ValueError as error:
        return _reject(str(error))
    base_count = Fraction(quantity_match.group(3))
    target_count = Fraction(target_match.group(1))
    if base_count <= 0 or target_count < 0:
        return _reject("unsafe recipe scaling values")
    scaled = _guard(base_quantity * target_count / base_count)
    unit = quantity_match.group(2)
    cost_match = re.search(
        rf"costs?\s+({NUMBER_PATTERN})\s+per\s+(?:{re.escape(unit)}|cup|kg|g|litre|liter)",
        text,
    )
    if cost_match:
        cost = _guard(scaled * Fraction(cost_match.group(1)))
        currency = "$" if "$" in text else ""
        return _accept_text(
            f"{_format_fraction(scaled)} {unit}; total cost {currency}{_format_fraction(cost)}.",
            "exact recipe scaling and unit-cost pattern",
        )
    return _accept_text(
        f"{_format_fraction(scaled)} {unit}.",
        "exact recipe scaling pattern",
    )


def _solve_unit_rate(text: str) -> LocalDecision | None:
    match = re.search(
        rf"({NUMBER_PATTERN})\s+([a-z]+)\s+(?:cost|costs)\s+({NUMBER_PATTERN}).*?(?:cost|price)\s+(?:of|for)\s+({NUMBER_PATTERN})\s+\2",
        text,
    )
    if not match:
        return None
    quantity = Fraction(match.group(1))
    total = Fraction(match.group(3))
    target = Fraction(match.group(4))
    if quantity <= 0:
        return _reject("unit-rate base quantity must be positive")
    return _accept(_guard(total * target / quantity), "exact unit-rate pattern")


def _solve_direct_expression(text: str) -> LocalDecision | None:
    cleaned_text = re.sub(
        r"\s*[.?!]?\s*(?:return|respond with|answer with|give)\s+only\s+(?:the\s+)?(?:number|numeric answer)\s*[.?!]?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    command_match = re.fullmatch(
        r"(?:please )?(?:what is|calculate|compute|evaluate|solve)\s+([-0-9.\s()+*/%]+)\??",
        cleaned_text,
    )
    if command_match:
        expression = command_match.group(1).strip()
    elif re.fullmatch(r"[-0-9.\s()+*/%]+", cleaned_text):
        expression = cleaned_text
    else:
        return None
    if not re.search(r"\d", expression):
        return _reject("expression contains no number")
    try:
        value = _safe_evaluate(expression)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error:
        return _reject(f"unsafe or unsupported expression: {error}")
    return _accept(value, "safe explicit arithmetic expression")


def solve_arithmetic(text: str) -> LocalDecision:
    if not isinstance(text, str):
        return _reject("task text is not a string")
    normalised = _normalise(text)
    if not normalised:
        return _reject("task text is empty")
    blocked_terms = (
        "write code", "python function", "javascript", "summarize", "summarise",
        "explain why", "prove that", "sentiment", "extract entities", "named entities",
    )
    if any(term in normalised for term in blocked_terms):
        return _reject("task belongs to another category")
    for solver in (
        _solve_recipe_scaling,
        _solve_inventory_sequence,
        _solve_percentage_of,
        _solve_chained_discount_tax,
        _solve_single_percentage_change,
        _solve_unit_rate,
        _solve_direct_expression,
    ):
        decision = solver(normalised)
        if decision is not None:
            return decision
    return _reject("no provably safe arithmetic pattern matched")
