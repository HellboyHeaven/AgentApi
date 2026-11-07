import ast
import math
import operator

from app.tools.base import Tool, ToolError

MAX_EXPRESSION_CHARS = 200
MAX_EXPONENT = 1000
MAX_RESULT_BITS = 4096  # caps integer powers, so '999 ** 999' cannot eat memory

_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CONSTANTS = {"pi": math.pi, "e": math.e}
_FUNCTIONS = {
    "sqrt": math.sqrt, "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
    "log": math.log, "log10": math.log10, "exp": math.exp,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
}


def _power(base: int | float, exponent: int | float) -> int | float:
    if abs(exponent) > MAX_EXPONENT:
        raise ToolError(f"The exponent is too large (the limit is {MAX_EXPONENT}).")
    if (
        isinstance(base, int) and isinstance(exponent, int)
        and exponent > 0 and base.bit_length() * exponent > MAX_RESULT_BITS
    ):
        raise ToolError("The result is too large to compute.")
    result = base ** exponent
    if isinstance(result, complex):  # e.g. (-8) ** 0.5
        raise ToolError("The result is not a real number.")
    return result


def _eval(node: ast.AST) -> int | float:
    """Evaluate a parsed expression. Only whitelisted node types are allowed."""
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant):
        # type() is exact on purpose: bool is a subclass of int, and complex is a separate type
        if type(node.value) in (int, float):
            return node.value
        raise ToolError("Only plain numbers are allowed, not strings, booleans or complex numbers.")

    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ToolError(f"Unknown name '{node.id}'. The available constants are: pi, e.")

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))

    if isinstance(node, ast.BinOp):
        op = type(node.op)
        left, right = _eval(node.left), _eval(node.right)
        if op is ast.Pow:
            return _power(left, right)
        if op in _BINARY:
            return _BINARY[op](left, right)
        if op is ast.BitXor:  # a very common mistake: '^' is XOR in Python
            raise ToolError("Use '**' for exponentiation, not '^'.")
        raise ToolError("Unsupported operator. Allowed: + - * / // % **")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise ToolError(f"Unknown function. Available: {', '.join(sorted(_FUNCTIONS))}.")
        if node.keywords or len(node.args) > 2:
            raise ToolError("Functions take positional arguments only, at most two.")
        return _FUNCTIONS[node.func.id](*[_eval(arg) for arg in node.args])

    # Attribute access, subscripts, lambdas, comprehensions, tuples, ... all end up here
    raise ToolError(
        "Unsupported syntax. Use numbers, + - * / // % **, parentheses, "
        "the constants pi and e, and the listed functions."
    )


def _format(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    if math.isinf(value) or math.isnan(value):
        raise ToolError("The result is not a finite number.")
    return format(value, ".12g")  # 12 significant digits hides float noise like 0.30000000000000004


def calculate(expression: str) -> str:
    expression = expression.strip()
    if not expression:
        raise ToolError("The expression is empty.")
    if len(expression) > MAX_EXPRESSION_CHARS:
        raise ToolError(f"The expression is longer than {MAX_EXPRESSION_CHARS} characters.")

    try:
        return _format(_eval(ast.parse(expression, mode="eval")))
    except ToolError:
        raise
    except SyntaxError:
        raise ToolError("Could not parse the expression. Write plain math, e.g. '17 * 23 / 4'.")
    except ZeroDivisionError:
        raise ToolError("Division by zero.")
    except (OverflowError, ValueError, TypeError) as e:
        raise ToolError(f"Math error: {e}")
    except (RecursionError, MemoryError):
        raise ToolError("The expression is too complex.")


CALCULATOR = Tool(
    name="calculator",
    description=(
        "Evaluate a math expression exactly. Use it for any arithmetic instead of computing "
        "in your head. Supports + - * / // % ** and parentheses, the constants pi and e, and "
        "the functions sqrt, abs, round, floor, ceil, log, log10, exp, sin, cos, tan "
        "(angles in radians). Pass only the expression, for example '17 * 23 / 4'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "maxLength": MAX_EXPRESSION_CHARS,
                "description": "The math expression to evaluate",
            }
        },
        "required": ["expression"],
        "additionalProperties": False,
    },
    func=calculate,
)