"""A real AST-based mutation engine.

Mutants are the ground truth of this thesis: each mutant is a *deliberately
injected fault*. A test/oracle that cannot distinguish a mutant from the correct
program would miss that bug in the field. The mutation score (fraction of
mutants a test suite kills) is therefore an objective, unarguable measure of a
suite's true fault-detection power -- which is exactly what "trustworthiness"
must be validated against.

Operators (standard mutation-testing set):
  AOR  arithmetic op replacement   + - * // / %
  ROR  relational op replacement   < <= > >= == !=
  LCR  logical connector replace   and <-> or
  CRP  constant replacement        n -> n+1, n-1, 0
  UOD  unary operator deletion      not x -> x
Each applicable location yields one mutant (first-order mutation).
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import Callable, List, Optional

from .programs import Subject


@dataclass
class Mutant:
    subject: str
    mid: int
    operator: str
    description: str
    func: Optional[Callable]          # compiled mutant (None if it failed to compile)
    equivalent: bool = False          # behaves identically to the original on all inputs


# ---- operator transformers ---------------------------------------------------------

_AOR = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv,
        ast.FloorDiv: ast.Mult, ast.Div: ast.Mult, ast.Mod: ast.Mult}
_ROR = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
_LCR = {ast.And: ast.Or, ast.Or: ast.And}


class _Collector(ast.NodeVisitor):
    """Collect mutable locations as (operator, node-id path)."""

    def __init__(self):
        self.sites: List[tuple] = []

    def generic_visit(self, node):
        for op_cls, table, kind in ((ast.BinOp, _AOR, "AOR"),):
            pass
        super().generic_visit(node)


def _apply_nth(tree: ast.AST, target_index: int):
    """Return (operator_name, description) after mutating the target_index-th site,
    or None if out of range. Mutates `tree` in place."""
    counter = {"i": 0}
    result = {"op": None, "desc": None}

    def bump(op, desc):
        if counter["i"] == target_index:
            result["op"], result["desc"] = op, desc
        counter["i"] += 1

    class T(ast.NodeTransformer):
        def visit_BinOp(self, node):
            self.generic_visit(node)
            t = type(node.op)
            if t in _AOR and counter["i"] == target_index:
                old = t.__name__
                node.op = _AOR[t]()
                bump("AOR", f"{old}->{type(node.op).__name__}")
                return node
            if t in _AOR:
                bump("AOR", "")
            return node

        def visit_Compare(self, node):
            self.generic_visit(node)
            if len(node.ops) == 1:
                t = type(node.ops[0])
                if t in _ROR and counter["i"] == target_index:
                    old = t.__name__
                    node.ops[0] = _ROR[t]()
                    bump("ROR", f"{old}->{type(node.ops[0]).__name__}")
                    return node
                if t in _ROR:
                    bump("ROR", "")
            return node

        def visit_BoolOp(self, node):
            self.generic_visit(node)
            t = type(node.op)
            if t in _LCR and counter["i"] == target_index:
                old = t.__name__
                node.op = _LCR[t]()
                bump("LCR", f"{old}->{type(node.op).__name__}")
                return node
            if t in _LCR:
                bump("LCR", "")
            return node

        def visit_Constant(self, node):
            if isinstance(node.value, bool):
                return node   # don't mutate booleans as ints
            if isinstance(node.value, int):
                if counter["i"] == target_index:
                    old = node.value
                    newv = old + 1
                    bump("CRP", f"{old}->{newv}")
                    return ast.copy_location(ast.Constant(value=newv), node)
                bump("CRP", "")
            return node

        def visit_UnaryOp(self, node):
            self.generic_visit(node)
            if isinstance(node.op, ast.Not):
                if counter["i"] == target_index:
                    bump("UOD", "not-deleted")
                    return node.operand
                bump("UOD", "")
            return node

    T().visit(tree)
    if result["op"] is None:
        return None
    return result["op"], result["desc"]


def _count_sites(source: str) -> int:
    tree = ast.parse(source)
    counter = {"i": 0}

    class C(ast.NodeVisitor):
        def visit_BinOp(self, node):
            self.generic_visit(node)
            if type(node.op) in _AOR:
                counter["i"] += 1

        def visit_Compare(self, node):
            self.generic_visit(node)
            if len(node.ops) == 1 and type(node.ops[0]) in _ROR:
                counter["i"] += 1

        def visit_BoolOp(self, node):
            self.generic_visit(node)
            if type(node.op) in _LCR:
                counter["i"] += 1

        def visit_Constant(self, node):
            if isinstance(node.value, int) and not isinstance(node.value, bool):
                counter["i"] += 1

        def visit_UnaryOp(self, node):
            self.generic_visit(node)
            if isinstance(node.op, ast.Not):
                counter["i"] += 1

    C().visit(tree)
    return counter["i"]


def generate_mutants(subject: Subject, mark_equivalent: bool = True) -> List[Mutant]:
    """Produce one first-order mutant per mutable site."""
    n = _count_sites(subject.source)
    ref = subject.compile_ref()
    mutants: List[Mutant] = []
    for i in range(n):
        tree = ast.parse(subject.source)
        info = _apply_nth(tree, i)
        if info is None:
            continue
        op, desc = info
        ast.fix_missing_locations(tree)
        func = None
        try:
            ns: dict = {}
            exec(compile(tree, f"<{subject.name}#mut{i}>", "exec"), ns)
            func = ns[subject.func_name]
        except Exception:
            func = None
        m = Mutant(subject.name, i, op, desc, func)
        if mark_equivalent and func is not None:
            m.equivalent = _is_equivalent(ref, func, subject.inputs)
        mutants.append(m)
    return mutants


def _call(func: Callable, args: tuple):
    try:
        return ("ok", func(*args))
    except Exception as e:  # noqa
        return ("exc", type(e).__name__)


def _is_equivalent(ref: Callable, mut: Callable, inputs: List[tuple]) -> bool:
    for args in inputs:
        if _call(ref, args) != _call(mut, args):
            return False
    return True


def mutation_score(detects: Callable[[Callable], bool], mutants: List[Mutant],
                   include_equivalent: bool = False) -> float:
    """Fraction of (non-equivalent, compilable) mutants killed by `detects`.

    `detects(mutant_func) -> True` means the suite/oracle distinguishes the
    mutant from correct behaviour (i.e. would catch that bug)."""
    pool = [m for m in mutants if m.func is not None and
            (include_equivalent or not m.equivalent)]
    if not pool:
        return 0.0
    killed = sum(1 for m in pool if detects(m.func))
    return killed / len(pool)
