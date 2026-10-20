"""The common currency of the whole thesis: a `Verdict`.

Every AI-testing modality (oracle generation, self-healing, adjudication) is
reduced to the same record, which is what lets a single trust metric generalise
across all three.

    apparent_ok      : did the AI testing process report GREEN / PASS / OK?
    ground_truth_ok  : was the program/element/verdict ACTUALLY correct?
    features         : observable signals available WITHOUT ground truth
                       (what the trust metric is allowed to use)
    trust            : the trust metric's score in [0,1] (filled in later)

A *false pass* is the dangerous case: apparent_ok == True while
ground_truth_ok == False -- a green result you must not believe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Verdict:
    modality: str
    subject: str
    apparent_ok: bool
    ground_truth_ok: bool
    features: Dict[str, float] = field(default_factory=dict)
    trust: Optional[float] = None
    info: Dict[str, object] = field(default_factory=dict)

    @property
    def false_pass(self) -> bool:
        """Reported OK but actually wrong -- the failure mode we must catch."""
        return self.apparent_ok and not self.ground_truth_ok

    @property
    def trustworthy(self) -> bool:
        """Ground-truth label the trust metric should predict for a green verdict."""
        return self.ground_truth_ok

    def as_dict(self) -> Dict[str, object]:
        return {
            "modality": self.modality,
            "subject": self.subject,
            "apparent_ok": self.apparent_ok,
            "ground_truth_ok": self.ground_truth_ok,
            "false_pass": self.false_pass,
            "trust": None if self.trust is None else round(self.trust, 4),
            "features": {k: round(v, 4) for k, v in self.features.items()},
        }
