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


def _reject(reason: str) -> LocalDecision:
    return LocalDecision(
        accepted=False,
        reason=reason,
    )


def _accept(
    value: Fraction,
    reason: str,
) -> LocalDecision:
    return LocalDecision(
        accepted=True,
        answer=_format_fraction(value),
        reason=reason,
    )


def _guard(value: Fraction) -> Fraction:
    if abs(value) > MAX_ABSOLUTE_VALUE:
        raise ValueError("result exceeds safe magnitude")

    if value.denominator > 10**12:
        raise ValueError("denominator exceeds safe limit")

    return value


def _constant_to_fraction(value: object) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("boolean constants are not arithmetic")

    if not isinstance(value, (int, float)):
        raise ValueError("unsupported constant")

    fraction = Fraction(str(value))
    return _guard(fraction)


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

    raise ValueError(
        f"unsupported syntax: {type(node).__name__}"
    )


def _safe_evaluate(expression: str) -> Fraction:
    if len(expression) > 200:
        raise ValueError("expression too long")

    if "^" in expression:
        raise ValueError("caret exponent syntax is ambiguous")

    parsed = ast.parse(
        expression,
        mode="eval",
    )

    return _evaluate_node(parsed)


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
            decimal_value = (
                Decimal(value.numerator)
                / Decimal(value.denominator)
            )

        formatted = format(decimal_value, "f")
        formatted = formatted.rstrip("0").rstrip(".")

        return formatted or "0"

    return format(float(value), ".12g")


def _normalise(text: str) -> str:
    replacements = {
        "×": "*",
        "÷": "/",
        "−": "-",
        "–": "-",
        "—": "-",
        "₹": "",
        "$": "",
        "€": "",
        "£": "",
        ",": "",
    }

    normalised = text.strip().lower()

    for old, new in replacements.items():
        normalised = normalised.replace(old, new)

    normalised = re.sub(
        r"\s+",
        " ",
        normalised,
    )

    return normalised.strip()


def _extract_numbers(text: str) -> list[Fraction]:
    return [
        Fraction(value)
        for value in re.findall(
            NUMBER_PATTERN,
            text,
        )
    ]


def _solve_percentage_of(text: str) -> LocalDecision | None:
    match = re.fullmatch(
        rf"(?:what is |calculate |compute )?"
        rf"({NUMBER_PATTERN})\s*%\s+of\s+"
        rf"({NUMBER_PATTERN})\??",
        text,
    )

    if not match:
        return None

    percentage = Fraction(match.group(1))
    base = Fraction(match.group(2))

    return _accept(
        _guard(base * percentage / 100),
        "exact percentage-of pattern",
    )


def _solve_chained_discount_tax(
    text: str,
) -> LocalDecision | None:
    has_discount = "discount" in text
    has_tax = "tax" in text or "gst" in text
    has_sequence = "then" in text or "after" in text

    if not (
        has_discount
        and has_tax
        and has_sequence
    ):
        return None

    numbers = _extract_numbers(text)

    if len(numbers) != 3:
        return _reject(
            "discount-tax pattern did not contain exactly three numbers"
        )

    base, discount, tax = numbers

    if base < 0:
        return _reject("negative base amount rejected")

    if not (
        0 <= discount <= 100
        and 0 <= tax <= 100
    ):
        return _reject("percentage outside safe range")

    discounted = base * (
        Fraction(1) - discount / 100
    )

    final_value = discounted * (
        Fraction(1) + tax / 100
    )

    return _accept(
        _guard(final_value),
        "exact chained discount-tax pattern",
    )


def _solve_single_percentage_change(
    text: str,
) -> LocalDecision | None:
    increase_words = (
        "increase",
        "increased",
        "add",
        "markup",
    )

    decrease_words = (
        "decrease",
        "decreased",
        "discount",
        "discounted",
        "reduce",
        "reduced",
    )

    increase = any(
        word in text
        for word in increase_words
    )

    decrease = any(
        word in text
        for word in decrease_words
    )

    if increase == decrease:
        return None

    if "%" not in text:
        return None

    numbers = _extract_numbers(text)

    if len(numbers) != 2:
        return _reject(
            "percentage-change pattern did not contain exactly two numbers"
        )

    base, percentage = numbers

    if base < 0:
        return _reject("negative base amount rejected")

    if not 0 <= percentage <= 100:
        return _reject("percentage outside safe range")

    multiplier = (
        Fraction(1) + percentage / 100
        if increase
        else Fraction(1) - percentage / 100
    )

    return _accept(
        _guard(base * multiplier),
        "exact single percentage-change pattern",
    )


def _solve_direct_expression(
    text: str,
) -> LocalDecision | None:
    command_match = re.fullmatch(
        r"(?:please )?"
        r"(?:what is|calculate|compute|evaluate|solve)"
        r"\s+([0-9.\s()+\-*/%]+)\??",
        text,
    )

    if command_match:
        expression = command_match.group(1).strip()
    elif re.fullmatch(
        r"[0-9.\s()+\-*/%]+",
        text,
    ):
        expression = text
    else:
        return None

    if not re.search(r"\d", expression):
        return _reject("expression contains no number")

    try:
        value = _safe_evaluate(expression)
    except (
        SyntaxError,
        TypeError,
        ValueError,
        ZeroDivisionError,
        OverflowError,
    ) as error:
        return _reject(
            f"unsafe or unsupported expression: {error}"
        )

    return _accept(
        value,
        "safe explicit arithmetic expression",
    )


def solve_arithmetic(
    text: str,
) -> LocalDecision:
    if not isinstance(text, str):
        return _reject("task text is not a string")

    normalised = _normalise(text)

    if not normalised:
        return _reject("task text is empty")

    blocked_terms = (
        "write code",
        "python function",
        "javascript",
        "summarize",
        "explain why",
        "prove that",
        "sentiment",
        "extract entities",
    )

    if any(
        term in normalised
        for term in blocked_terms
    ):
        return _reject(
            "task belongs to another category"
        )

    solvers = (
        _solve_percentage_of,
        _solve_chained_discount_tax,
        _solve_single_percentage_change,
        _solve_direct_expression,
    )

    for solver in solvers:
        decision = solver(normalised)

        if decision is not None:
            return decision

    return _reject(
        "no provably safe arithmetic pattern matched"
    )
