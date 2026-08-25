"""Orbit budget: repeat, or close the arc.

Restated from the original brief, which did not typecheck (flag ⑤). The brief
said `R > ŵ · M_budget` -- but M is a hard gate, and a binary thing has no
budget. So the budget is denominated in ACCUMULATED REPETITION COST, and the
decision compares the marginal cost of the next utterance against what is left.

What "close the orbit" means in a shipped product is that the system declines to
keep talking about this referent. That is a PRODUCT decision wearing a loss
term's clothing, so the policy is explicit and named rather than implied by a
threshold buried in the loop.
"""
from __future__ import annotations
import enum
from dataclasses import dataclass, field


class Decision(str, enum.Enum):
    ACCEPT = "ACCEPT"          # fits inside the budget
    REPEAT = "REPEAT"          # over budget; policy keeps the arc alive anyway
    CLOSE = "CLOSE"            # over budget; policy ends the arc


class Policy(str, enum.Enum):
    KEEP_ALIVE = "KEEP_ALIVE"  # accept repetition rather than stop talking
    CLOSE_ORBIT = "CLOSE_ORBIT"


@dataclass
class Orbit:
    """One conversational arc. Budget is in accumulated novelty cost."""
    orbit_id: str
    budget: float = 3.0
    policy: Policy = Policy.CLOSE_ORBIT
    spent: float = 0.0
    turns: int = 0
    closed: bool = False
    history: list[tuple[str, float, str]] = field(default_factory=list)

    def remaining(self) -> float:
        return max(0.0, self.budget - self.spent)

    def offer(self, referent_id: str, cost: float) -> Decision:
        """Decide whether an utterance costing `cost` may be said in this arc.

        Does NOT mutate: the caller commits with `commit` once the utterance
        actually passes the M gate. Keeps rejected candidates from draining the
        budget.
        """
        if self.closed:
            return Decision.CLOSE
        if cost <= self.remaining():
            return Decision.ACCEPT
        return (Decision.REPEAT if self.policy is Policy.KEEP_ALIVE
                else Decision.CLOSE)

    def commit(self, referent_id: str, cost: float, decision: Decision) -> None:
        if self.closed:
            raise RuntimeError(f"orbit {self.orbit_id} is closed")
        self.history.append((referent_id, cost, decision.value))
        if decision is Decision.CLOSE:
            self.closed = True
            return
        self.spent += cost
        self.turns += 1

    def to_dict(self) -> dict:
        return {"orbit_id": self.orbit_id, "budget": self.budget,
                "policy": self.policy.value, "spent": self.spent,
                "turns": self.turns, "closed": self.closed,
                "history": self.history}

    @staticmethod
    def from_dict(d: dict) -> "Orbit":
        return Orbit(orbit_id=d["orbit_id"], budget=d["budget"],
                     policy=Policy(d["policy"]), spent=d["spent"],
                     turns=d["turns"], closed=d["closed"],
                     history=[tuple(h) for h in d["history"]])
