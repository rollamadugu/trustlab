"""Subjects under test (SUTs).

Each subject is a small, deterministic, fully-specified function. We keep the
source as a string so the mutation engine can parse and mutate it with Python's
`ast` module, and we keep an independent reference `spec` so we always have a
ground-truth correct answer (the "specification oracle"). Inputs are drawn from
a declared domain so test suites can be generated reproducibly.

These play the role of a classic mutation-testing benchmark: small enough to
reason about, rich enough (branches, arithmetic, comparisons, booleans) that
mutation produces meaningful faults.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Tuple


@dataclass
class Subject:
    name: str
    source: str                       # function source (mutation target)
    func_name: str                    # the function's name inside source
    spec: Callable                    # independent reference implementation
    inputs: List[tuple]               # candidate input tuples for test generation
    out_kind: str = "int"             # "int" | "float" | "str" | "bool" (for weak oracles)

    def compile_ref(self) -> Callable:
        ns: dict = {}
        exec(compile(self.source, f"<{self.name}>", "exec"), ns)
        return ns[self.func_name]


# ---- subject definitions -----------------------------------------------------------

_GRADE_SRC = '''
def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
'''

def _grade_spec(score):
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"


_BMI_SRC = '''
def classify_bmi(weight, height):
    bmi = weight / (height * height)
    if bmi < 18.5:
        return "under"
    elif bmi < 25.0:
        return "normal"
    elif bmi < 30.0:
        return "over"
    else:
        return "obese"
'''

def _bmi_spec(weight, height):
    bmi = weight / (height * height)
    return "under" if bmi < 18.5 else "normal" if bmi < 25.0 else "over" if bmi < 30.0 else "obese"


_LEAP_SRC = '''
def is_leap_year(y):
    if y % 400 == 0:
        return True
    if y % 100 == 0:
        return False
    if y % 4 == 0:
        return True
    return False
'''

def _leap_spec(y):
    return (y % 400 == 0) or (y % 100 != 0 and y % 4 == 0)


_DISCOUNT_SRC = '''
def discount(price, qty):
    if qty >= 100:
        rate = 20
    elif qty >= 50:
        rate = 10
    elif qty >= 10:
        rate = 5
    else:
        rate = 0
    return price - (price * rate) // 100
'''

def _discount_spec(price, qty):
    rate = 20 if qty >= 100 else 10 if qty >= 50 else 5 if qty >= 10 else 0
    return price - (price * rate) // 100


_TRI_SRC = '''
def triangle_type(a, b, c):
    if a + b <= c or a + c <= b or b + c <= a:
        return "invalid"
    if a == b and b == c:
        return "equilateral"
    if a == b or b == c or a == c:
        return "isosceles"
    return "scalene"
'''

def _tri_spec(a, b, c):
    if a + b <= c or a + c <= b or b + c <= a:
        return "invalid"
    if a == b and b == c:
        return "equilateral"
    if a == b or b == c or a == c:
        return "isosceles"
    return "scalene"


_FIZZ_SRC = '''
def fizzbuzz(n):
    if n % 15 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    else:
        return str(n)
'''

def _fizz_spec(n):
    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)


SUBJECTS: List[Subject] = [
    Subject("grade", _GRADE_SRC, "grade", _grade_spec,
            [(s,) for s in (0, 55, 59, 60, 61, 69, 70, 79, 80, 89, 90, 95, 100)], "str"),
    Subject("classify_bmi", _BMI_SRC, "classify_bmi", _bmi_spec,
            [(w, h) for w in (45, 60, 70, 85, 110) for h in (1.6, 1.75, 1.9)], "str"),
    Subject("is_leap_year", _LEAP_SRC, "is_leap_year", _leap_spec,
            [(y,) for y in (1900, 1996, 2000, 2001, 2004, 2024, 2100, 2400, 1999)], "bool"),
    Subject("discount", _DISCOUNT_SRC, "discount", _discount_spec,
            [(p, q) for p in (100, 250, 999) for q in (1, 5, 10, 49, 50, 99, 100, 200)], "int"),
    Subject("triangle_type", _TRI_SRC, "triangle_type", _tri_spec,
            [(a, b, c) for a in (2, 3, 5) for b in (2, 4, 5) for c in (2, 3, 6)], "str"),
    Subject("fizzbuzz", _FIZZ_SRC, "fizzbuzz", _fizz_spec,
            [(n,) for n in (1, 2, 3, 5, 9, 15, 30, 31, 45, 98, 100)], "str"),
]


def subject_by_name(name: str) -> Subject:
    for s in SUBJECTS:
        if s.name == name:
            return s
    raise KeyError(name)
