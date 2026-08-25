"""Run the 2a loop and report. No GPU, no model."""
from __future__ import annotations
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tlon.audit import log as audit                     # noqa: E402
from tlon.grammar import classes as C                   # noqa: E402
from tlon.novelty.orbit import Policy                   # noqa: E402
from tlon.selfplay.loop import Config, run              # noqa: E402

RUNS = pathlib.Path(__file__).resolve().parents[1] / "runs"


def main() -> int:
    RUNS.mkdir(exist_ok=True)
    db = RUNS / "2a.db"
    if db.exists():
        db.unlink()
    con = audit.connect(db)
    cfg = Config(turns=600)
    run_id = "2a-0001"

    st, rep = run(con, cfg, run_id=run_id)

    q = lambda s, *a: con.execute(s, a).fetchone()
    print("=" * 74)
    print(f"2a RUN {run_id} — structural compat, no model")
    print(f"lexicon {C.load()['_hash']}")
    print("=" * 74)
    print(f"  turns requested        {cfg.turns}")
    print(f"  utterances accepted    {st.accepted}")
    print(f"  proposals made         {st.attempts}")
    print(f"  rejected: M gate       {st.m_fail}")
    print(f"  rejected: too repetitive {st.novelty_reject}")
    print(f"  orbits closed          {st.orbits_closed}")
    print(f"  repeats allowed        {st.repeats_allowed}")

    acc = q("SELECT COUNT(*) c FROM utterance WHERE accepted=1")["c"]
    coll = q("SELECT COUNT(*) c FROM utterance WHERE accepted=1 AND collision=1")["c"]
    uniq = q("SELECT COUNT(DISTINCT utterance_id) c FROM utterance WHERE accepted=1")["c"]
    print("\n  --- collision counter (monitoring, decoupled from R) ---")
    print(f"  accepted utterances    {acc}")
    print(f"  distinct meanings      {uniq}")
    print(f"  exact canonical repeats {coll}")

    amb = q("SELECT COUNT(*) c FROM utterance WHERE accepted=1 AND ambiguity>1")["c"]
    print(f"\n  --- referent ambiguity (03/15 overlap is BY RULING) ---")
    print(f"  utterances matching >1 referent  {amb}  "
          f"({100 * amb / max(1, acc):.1f}%)")
    for k, v in sorted(st.ambiguity_pairs.items(), key=lambda x: -x[1])[:6]:
        print(f"      {k}: {v}")

    print(f"\n  --- repetition log (bounded, decaying) ---")
    print(f"  buckets                {len(rep.buckets)}")
    print(f"  medoids held           {rep.total_medoids()}  "
          f"(cap {cfg.k_per_bucket}/bucket = {cfg.k_per_bucket * len(rep.buckets)})")

    print("\n  --- sample of what it said ---")
    for r in con.execute(
            "SELECT referent_id, surface, gloss FROM utterance "
            "WHERE accepted=1 ORDER BY RANDOM() LIMIT 5"):
        print(f"    [{r['referent_id']}] {r['surface']}")
        print(f"        \"{r['gloss']}\"")

    print("\n" + "=" * 74)
    print("ADVERSARIAL PROBES — the run above proves almost nothing on its own")
    print("=" * 74)
    print("  M rejected 0/600 because the sampler BUILDS from the signature and")
    print("  then verifies it: the gate could not have fired. A 100% pass rate")
    print("  from a test that cannot fail is not evidence. Same for 0% ambiguity")
    print("  and 0 novelty rejections. These probes make each one falsifiable.\n")

    import random as _r
    from tlon.referents import match, schema as _sc
    from tlon.selfplay import scenes as _scn
    rs = _sc.load()
    seeds = rs.seeds()
    rng = _r.Random(7)

    # 1. can the M gate reject at all?
    wrong = 0
    for i in range(200):
        a, b = rng.sample(seeds, 2)
        sc = _scn.sample(a, rng)
        if b.id not in {x.id for x in match.resolve(sc, seeds)}:
            wrong += 1
    print(f"  1. M REJECTS A MISMATCHED REFERENT: {wrong}/200 "
          f"({'PASS' if wrong > 190 else 'FAIL — gate is not discriminating'})")

    # 2. is the deliberate 03/15 overlap reachable at all?
    r03 = next(r for r in seeds if r.id == "03")
    r15 = next(r for r in seeds if r.id == "15")
    both = "mil flex sen fang u fang mlö ka"
    from tlon.grammar.parse import parse as _p
    hits = sorted(x.id for x in match.resolve(_p(both), seeds))
    print(f"  2. 03/15 OVERLAP IS REACHABLE: {both}")
    print(f"     resolves to {hits}  "
          f"({'PASS' if hits == ['03', '15'] else 'FAIL'})")
    print("     ...but the sampler never built one in 600 turns, so the 0%")
    print("     ambiguity above measures the SAMPLER, not the signatures.")

    # 3. does R bind when the space is actually small?
    db2 = RUNS / "2a_stress.db"
    if db2.exists():
        db2.unlink()
    con2 = audit.connect(db2)
    st2, rep2 = run(con2, Config(turns=400, decorate_p=0.0, arc_len=8,
                                 novelty_reject=0.5, seed=99),
                    run_id="2a-stress", refs=seeds[:3])
    print(f"\n  3. R BINDS UNDER LOW ENTROPY (3 referents, no decoration):")
    print(f"     accepted             {st2.accepted}")
    print(f"     novelty rejections   {st2.novelty_reject}  "
          f"({'PASS' if st2.novelty_reject > 0 else 'FAIL — R never engaged'})")
    print(f"     orbits closed        {st2.orbits_closed}  "
          f"({'PASS' if st2.orbits_closed > 0 else 'FAIL — orbit never fired'})")
    c2 = con2.execute("SELECT COUNT(*) c FROM utterance WHERE accepted=1 "
                      "AND collision=1").fetchone()["c"]
    print(f"     exact repeats        {c2}")
    print(f"     medoids held         {rep2.total_medoids()} (bounded)")
    con2.close()

    audit.record_counter(
        con, run_id=run_id, utterances_total=acc,
        days_without_repeat=0.0 if coll else 1.0,
        m_pass_rate=1 - st.m_fail / max(1, st.attempts),
        m_sample_n=st.attempts, auditor_state=audit.AUDITOR_ABSENT)
    print("\n  --- B2: can this be published? ---")
    try:
        audit.publish_counter(con, run_id)
        print("    ERROR: 2a published a counter. That must never happen.")
        return 1
    except audit.AuditError as e:
        print(f"    correctly refused — {str(e)[:120]}...")

    con.close()
    print(f"\n  audit db: {db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
