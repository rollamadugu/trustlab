"""Modality 2 -- AI self-healing UI tests (silent mis-heals).

A UI test targets one element. After a UI change the original locator breaks and
a self-healer re-finds an element by attribute similarity. The danger is a
*silent mis-heal*: the healer confidently picks the WRONG element, the action
still succeeds, and the test stays GREEN while testing the wrong thing.

Ground truth here is the element's stable hidden identity (`eid`), which a real
tool never sees. The trust metric may use only observable signals: match
confidence, ambiguity (gap to the runner-up), number of candidates, attributes
agreed. This models the documented finding that unconstrained self-healing
autonomy produces "misleading outcomes".
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List

from ..verdict import Verdict

# attribute -> weight when scoring similarity (an id is strong evidence, a
# position is weak). These are observable; the eid is NOT.
_WEIGHTS = {"id": 0.40, "text": 0.25, "role": 0.15, "cls": 0.12, "pos": 0.08}
_ROLES = ["button", "link", "input", "checkbox", "tab", "menuitem"]
_WORDS = ["submit", "cancel", "save", "delete", "next", "back", "login",
          "search", "ok", "close", "apply", "reset", "continue", "edit"]


@dataclass
class _El:
    eid: int                       # hidden stable identity (GROUND TRUTH only)
    attrs: Dict[str, object]


def _rand_el(eid: int, rng: random.Random) -> _El:
    return _El(eid, {
        "id": f"el{rng.randint(0, 9999)}",
        "text": rng.choice(_WORDS),
        "role": rng.choice(_ROLES),
        "cls": f"c{rng.randint(0, 40)}",
        "pos": rng.randint(0, 30),
    })


def _similarity(remembered: Dict[str, object], el: _El) -> float:
    s = 0.0
    for k, w in _WEIGHTS.items():
        if remembered.get(k) == el.attrs.get(k):
            s += w
    return s


def _perturb(el: _El, rng: random.Random, intensity: float) -> _El:
    a = dict(el.attrs)
    for k in list(a.keys()):
        if rng.random() < intensity:
            if k == "id":
                a["id"] = f"el{rng.randint(0, 9999)}"
            elif k == "text":
                a["text"] = rng.choice(_WORDS)
            elif k == "role":
                a["role"] = rng.choice(_ROLES)
            elif k == "cls":
                a["cls"] = f"c{rng.randint(0, 40)}"
            else:
                a["pos"] = rng.randint(0, 30)
    return _El(el.eid, a)


def _one_scenario(rng: random.Random, heal_threshold: float = 0.25) -> Verdict:
    n = rng.randint(4, 10)
    page = [_rand_el(i, rng) for i in range(n)]
    target = rng.choice(page)
    remembered = dict(target.attrs)              # locator snapshot the test stored

    # UI change: perturb the whole page; the target's own attributes may change
    # a lot (breaking the original locator) and distractors may look similar.
    intensity = rng.uniform(0.2, 0.8)
    changed = [_perturb(el, rng, intensity) for el in page]

    scores = sorted(((_similarity(remembered, el), el) for el in changed),
                    key=lambda t: t[0], reverse=True)
    top_score, top_el = scores[0]
    runner = scores[1][0] if len(scores) > 1 else 0.0

    healed = top_score >= heal_threshold          # did the healer pick something?
    apparent_ok = healed                           # a found element => action succeeds => GREEN
    picked_correct = healed and top_el.eid == target.eid
    ground_truth_ok = picked_correct

    features = {
        "match_confidence": top_score,
        "ambiguity": top_score - runner,          # small gap => risky heal
        "n_candidates": float(n),
        "attrs_agreed": float(sum(1 for k in _WEIGHTS
                                  if remembered.get(k) == top_el.attrs.get(k))),
        "change_intensity_proxy": 1.0 - top_score,  # observable proxy only
    }
    return Verdict(modality="heal", subject="ui",
                   apparent_ok=apparent_ok, ground_truth_ok=ground_truth_ok,
                   features=features,
                   info={"picked_correct": picked_correct, "healed": healed})


def generate_healing_verdicts(rng: random.Random, n: int = 400) -> List[Verdict]:
    return [_one_scenario(rng) for _ in range(n)]
