"""THE SPEND CEILING — and the two bugs that got past it, replayed.

⛔⛔ THIS IS A MONEY GUARD AND IT FAILED IN BOTH DIRECTIONS IN ONE DAY.

  1. The proposal stage called `settle(cumulative)` which ASSIGNED
     `_spent = cumulative`, wiping out everything the seed stage had already
     spent. The build reported $59.96 against a $60 cap and had actually spent
     that PLUS $6.29 of seeds — a real overrun, reported as a clean stop.

  2. The dialogue stage called `settle(budget.spent + running_total)` where
     `running_total` was cumulative, re-adding the whole spend every iteration.
     The figure inflated quadratically, the cap locked out a run that had
     produced zero output, and the reported $68.71 was fiction.

⭐ ONE BUG UNDER-COUNTED AND THE OTHER OVER-COUNTED, AND BOTH LOOKED LIKE THE
CAP WORKING. That is the reason these are tests and not a comment: a ceiling
nobody can see through is indistinguishable from a ceiling that holds.
"""
from __future__ import annotations

import concurrent.futures as cf
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from act2_build_natural_corpus import Budget, BudgetExceeded    # noqa: E402


def test_add_accumulates_and_does_not_assign():
    """⛔ BUG 1. A method that assigns cannot be called twice by two stages."""
    b = Budget(10.0)
    b.add(1.0)
    b.add(2.0)
    assert b.spent == pytest.approx(3.0)


def test_two_stages_both_count():
    """⛔⛤ THE EXACT SHAPE OF BUG 1: a seed stage spends, then a proposal stage
    reports its own cumulative ledger. The seed spend must survive."""
    b = Budget(10.0)
    b.add(6.29)                          # seeds
    b.settle_proposer(3.0)               # proposer's cumulative ledger
    b.settle_proposer(5.0)
    assert b.spent == pytest.approx(11.29), (
        "⛔⛔ the proposer's ledger overwrote the seed stage's spend")


def test_settle_proposer_applies_only_the_increment():
    """⛔ BUG 2's shape. A cumulative ledger read repeatedly must not be added
    repeatedly."""
    b = Budget(100.0)
    for total in (1.0, 1.0, 2.5, 2.5, 2.5, 4.0):
        b.settle_proposer(total)
    assert b.spent == pytest.approx(4.0)


def test_settle_proposer_is_monotonic_under_out_of_order_reads():
    """⭐ With N workers, one thread can read the shared ledger AFTER another
    has already advanced it. A stale read must contribute nothing, not unwind
    the total."""
    b = Budget(100.0)
    b.settle_proposer(5.0)
    b.settle_proposer(3.0)               # stale read from another thread
    assert b.spent == pytest.approx(5.0)


def test_the_cap_refuses_before_the_call_not_after():
    """⛔ A cap checked afterwards reports an overrun instead of preventing
    one. `reserve()` is what must refuse."""
    b = Budget(0.05, estimate_per_call=0.01)
    for _ in range(5):
        b.reserve()
        b.add(0.01)
    with pytest.raises(BudgetExceeded):
        b.reserve()


def test_reservations_bound_the_overrun_with_workers_in_flight():
    """⭐ The honest promise: worst case is (workers × one call), not unbounded.
    Ten reservations are taken before any settles, and the eleventh refuses."""
    b = Budget(0.10, estimate_per_call=0.01)
    for _ in range(10):
        b.reserve()
    with pytest.raises(BudgetExceeded):
        b.reserve()


def test_concurrent_spend_never_exceeds_the_cap():
    """⛔⛤ THE WHOLE POINT, UNDER THREADS. Twenty workers each try to spend
    more than the cap allows; the total admitted must not exceed it."""
    b = Budget(1.00, estimate_per_call=0.01)
    admitted = []

    def worker(_i):
        try:
            b.reserve()
        except BudgetExceeded:
            return 0.0
        b.add(0.01)
        admitted.append(0.01)
        return 0.01

    with cf.ThreadPoolExecutor(max_workers=20) as ex:
        list(ex.map(worker, range(500)))

    assert b.spent <= 1.00 + 1e-9, "⛔⛤ the cap was breached: $%.4f" % b.spent
    # ⭐ 99, NOT 100 — AND THAT IS CORRECT. Adding 0.01 a hundred times does not
    # reach 1.00 exactly in binary floating point, so the last reservation sees
    # a total a hair over the limit and refuses. A money ceiling that rounds
    # toward spending less is the right direction to be wrong in; asserting an
    # exact 100 here would be asserting float equality and would make the guard
    # look broken for behaving well.
    assert 99 <= len(admitted) <= 100


def test_a_zero_budget_admits_nothing():
    """⛔ The degenerate case a `--budget-usd 0` would produce. It must refuse
    the first call rather than allow one 'free' one."""
    b = Budget(0.0)
    with pytest.raises(BudgetExceeded):
        b.reserve()


def test_there_is_no_method_that_assigns_spent():
    """⭐⭐ THE STRUCTURAL GUARD. Both bugs were possible because one method
    took 'the new total'. If a future edit reintroduces `settle(actual)`, this
    fails — the mistake becomes unspellable rather than merely documented."""
    assert not hasattr(Budget, "settle"), (
        "⛔⛤ `Budget.settle` is back. It assigned the total, and two stages "
        "calling it under different conventions cost real money twice.")
    assert hasattr(Budget, "add")
    assert hasattr(Budget, "settle_proposer")
