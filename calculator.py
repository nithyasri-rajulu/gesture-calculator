"""Safe calculator state and a pinch gate independent of the camera backend."""
import ast
import math
import operator
from dataclasses import dataclass

OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
       ast.Mult: operator.mul, ast.Div: operator.truediv}

def calculate(expression: str) -> str:
    if not expression or len(expression) > 80:
        raise ValueError('Enter an expression of at most 80 characters')
    tree = ast.parse(expression, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ValueError('Expression too complex')
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in OPS:
            value = OPS[type(node.op)](visit(node.left), visit(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        else:
            raise ValueError('Only numbers and + - * / are allowed')
        if not math.isfinite(value) or abs(value) > 1e12:
            raise ValueError('Result is outside the supported range')
        return value
    return format(visit(tree.body), '.12g')

@dataclass
class Calculator:
    expression: str = ''
    error: str = ''
    evaluated: bool = False

    def press(self, key):
        self.error = ''
        if key == 'C':
            self.expression = ''; self.evaluated = False
        elif key == 'DEL':
            self.expression = self.expression[:-1]; self.evaluated = False
        elif key == '=':
            try:
                self.expression = calculate(self.expression); self.evaluated = True
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
                self.error = 'Invalid expression or division by zero'
        elif key in '0123456789.+-*/()' and len(key) == 1:
            if self.evaluated and key not in '+-*/': self.expression = ''
            self.evaluated = False
            if len(self.expression) < 80: self.expression += key

class PinchGate:
    """One event per release/pinch, after a stable hover. Missing hands disarm."""
    def __init__(self, stable_seconds=.12, close_ratio=.35, open_ratio=.55):
        self.stable_seconds = stable_seconds
        self.close_ratio, self.open_ratio = close_ratio, open_ratio
        self.armed = False
        self.target = None
        self.since = 0.

    def update(self, key, ratio, timestamp):
        if ratio is None:
            self.armed = False; self.target = None
            return None
        if key != self.target:
            self.target, self.since = key, timestamp
        if ratio >= self.open_ratio:
            self.armed = True
        if self.armed and ratio <= self.close_ratio:
            # A pinch outside a key is still consumed. Holding it while moving
            # into a key cannot cause an accidental activation.
            self.armed = False
            if key is not None and timestamp - self.since >= self.stable_seconds:
                return key
        return None
