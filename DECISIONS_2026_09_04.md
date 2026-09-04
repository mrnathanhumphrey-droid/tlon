# DECISIONS — 2026-09-04 · the termination-architecture arc, and the relaunch

One file per arc: the decision, the evidence, what was rejected, and the sha.
⛔ **Retractions are recorded, not quietly dropped.**

Entry point: `STATE.md`. Dictionary: `MEASUREMENTS.md`.
Previous arc: `DECISIONS_2026_09_03.md`. Loss record:
`runs/act2/retrain12/SALVAGE_2026_09_04.md`.

---

## D1 · `~/DONE` means PERSISTED, not COMPUTED

**Decision.** The box pushes its own artifacts to durable storage as a
**pipeline stage**, per adapter, inside the loop; `~/DONE` is written only after
a verify stage confirms every cell is on the hub.

**Evidence.** Two boxes self-terminated on 2026-09-04 with work still on them,
and **the watchdog was right both times** — `retrain12` had finished and the
ct-gate box had died, so both were billing for nothing. The defect was never the
eagerness. `~/DONE` meant COMPUTED while the collection it implied lived on
another machine, so every run had a five-minute window in which the only copy of
the work sat on a box already trying to end itself. Two systems had to agree
about something neither of them modelled.

**Rejected.** (a) Teach the watchdog about unpersisted work — a third check
across the same seam, and the seam is the problem. (b) A persist stage at the
END of the run — would still have lost the gate adapter, which died at
`manifest`, a stage that sits *between* the last adapter and the end.

**Also.** `--flush-cmd` gives the kill path last words, so a box killed for a
stall or a dead process still ships its run log — the one artifact re-running
cannot regenerate. It is best-effort by construction and **can never block the
terminate**: it fires on a box already burning money for nothing.

**sha** `bba4ef9`

## D2 · Sweep the class, and let the guard find its own members

**Decision.** The structural test **discovers** every pipeline that arms the
watchdog and holds each to persist-before-`~/DONE`.

**Evidence.** Both of the night's losses were classes already met and fixed in
exactly one place. Naming `pipeline_retrain.sh` in the guard would have repeated
that. The discovering guard immediately pulled in `pipeline_positive_control.sh`
— whose own header records that its log "has been lost to a kill once already" —
and then caught `pipeline_solo_regen.sh` the moment it was written.

**What the sweep found beyond the known defect.**
- ⛔ `glob("adapter_s*")` in the `manifest` stage stopped matching once the cell
  entered the directory name (`adapter_ct-s20624`), so the manifest was empty
  for **every** run under the new naming, not only the single-adapter one. The
  `== 6` assertion reported it; the glob caused it.
- ⛔ `cmd_env` silently shipped an empty `HF_TOKEN` (`hf = ""`). With
  persistence load-bearing that is a run which trains for hours and then cannot
  save. It refuses now, and the box **proves it can write** to the hub at
  provision time — a read-only token passes a read probe and fails at the end.
- ⛔ `poll` tailed, and `collect` scp'd, a hardcoded `pipeline_retrain.log`. The
  third instance was found *by the guard written for the second*.
- ⛔ A guard that could not tell an explanation from the thing it explains: the
  batch-size test fired on its own module's **docstring**. Stripping `#` lines is
  not enough; that guard and its sibling in `test_provision.py` parse the AST.

**sha** `bba4ef9`, `07c5489`

## D3 · Two boxes in parallel, not one box serially

**Decision.** Item 2 (solo regen) and item 3 (the ct gate) run on separate
`gpu_1x_a100_sxm4` instances at once.

**Evidence.** Billing is per GPU-hour, so the total is the same either way
(~4.0 + ~4.7 GPU-h at $1.99/h). Serially the gate lands ~8.7 h after launch;
in parallel ~4.7 h, leaving the whole evening to read it rather than the middle
of the night. The two runs share no state.

`solo_regen` `30abb29e1fac44679b399df52d677ece` · `161.153.104.106`
`retrain12_ct` `f4873ab73f414da38e30a275796feafe` · `141.148.161.107`

**sha** `1ee9827` (records committed at launch)

## D4 · The gate read runs on the box

**Decision.** `train --model-lag` sets `MODEL_LAG=1`; the pipeline runs
`act2_model_lag.py` after each adapter is **persisted**.

**Evidence.** The instrument needs the model and the adapter on a GPU. Left as a
step to run afterwards it means keeping a box alive for it or buying a second
one — and "a runbook step nobody had ever executed" is how s20620 was lost. It
runs after `persist_$CELL` so a fault in the read costs the read, not the
weights. Its parameters are pinned in the stage, not exposed as flags
(prereg `abde6124` §4).

**sha** `4248023`

## D5 · THE GATE FIRED — **STOP, CONTENT PERSISTS**. The eleven are not bought.

**Read against `docs/PREREG_CONTENT_TRANSIENT_MODEL_GATE_2026_09_03.md`
LOCK `abde6124`** (verifies). Artifact: `runs/act2/retrain12_ct/
model_lag_ct-s20624.json`, also `hf://…/ct-s20624/`.

⭐ **Chain accounting first, as §2 requires:** 12 of 12 chains used, **0 dropped**,
120 turns. The full design. No turn was refused into a short chain, so nothing
here is an artefact of a truncated instrument.

| lag | CORPUS (what was trained) | MODEL (what was learned) |
|---|---|---|
| 1 | 0.962  z = **+516.30** | 1.028  z = **+22.86** |
| 2 | 0.027  z = **−11.22** | 0.385  z = **+6.56** |
| 3 | 0.042  z = −3.87 | 0.238  z = +2.43 |
| 4 | 0.048  z = −0.70 | 0.222  z = +2.08 |

Thresholds (imported, not invented): lag1 z ≥ 6.0 · every longer lag z ≤ 3.0.

**Verdict: `REFUSED` — reading (c), STOP-persists.** lag 1 clears easily; **lag 2
lands at z = +6.56 against a ceiling of 3.0**, more than double it.

**What this actually answers.** The open question was "does corpus lag-1
responsiveness reach the model?" — and the answer is **yes**. That is a real
result: the content-free arm produced 0.00 shared roots over 13 exchanges, and
this model perceives its provocation at z = +22.86. The transmission channel
works.

⛔⛔ **BUT THE RELEASE DID NOT TRANSMIT, AND RELEASE IS THE TLÖNIAN HALF.** The
corpus does not merely fail to carry content at lag 2 — it is **actively
suppressed**, z = −11.22, *below* chance, which is the containment bar doing its
job. The model came out at +6.56. ⭐ In an alternating exchange **lag 2 is the
speaker's OWN previous turn**, so this is the model holding onto what it itself
just said: object permanence, rebuilt from local choices. That is the thing Tlön
denies. The recipe did not fail toward the control — it **overshot past the
target into the un-Tlön failure mode**.

⚠️ **POST-HOC, NOT PART OF THE VERDICT:** lags 3 and 4 sit at +2.43 and +2.08 —
under the ceiling individually, but positive where the corpus was negative. The
model's persistence looks **diffuse** (a raised self-similarity floor around
0.22) rather than a clean one-step carry. That is an observation to design
against, not a finding; it was not pre-declared and nothing follows from it.

**Consequences, per the locked document.**
- The remaining eleven adapters are **NOT bought**.
- The chatbot deliverable is **NOT unblocked**.
- ⛔⛔ **NO THRESHOLD CHANGE IS AUTHORISED.** The prereg says so, and the margin
  makes it moot: 6.56 against 3.0 is not a near miss.
- ⛔ The underpowered clause does **not** apply — it covers lag-1 landing between
  3 and 6, and lag 1 is +22.86.

**sha** to follow; artifacts saved locally and hub-verified.

---

# ⛔⛔ RETRACTIONS AND CORRECTIONS

## R1 · My first artefact guard would have skipped nothing, and my second would have skipped too much

**Claimed.** The two tests that failed on the box need corpus directories that
are absent from a fresh clone.

**Actually.** The corpus **directories are tracked** (`manifest.json` is
committed); only `train.jsonl` is gitignored, and that is what `corpus_for`
reads. A guard on the directory would have been satisfied on the box and skipped
nothing.

**And worse in the other direction.** I had decorated a third test that **passes
on a fresh clone** — the alias returns its recorded seed even when `train.jsonl`
is absent. That decorator would have converted a real floor check into a silent
skip on every box. ⭐ **An over-broad skip is worse than the failure it copies:**
the failure stops the run, the skip does not.

## R2 · The simulation was wrong, not the box — and that is how the real defect surfaced

**Claimed, implicitly.** Cloning the repo on this laptop simulates what a rented
Linux box gets.

**Actually.** The Windows clone reported **24 failed / 1496 passed / 6 skipped**
where the box reported **2 failed / 1520 passed / 4 skipped**. The simulation was
the thing that was lying.

**Why, and it is not a simulation bug.** `classes.load()` hashes
`lexicon.yaml`'s raw bytes, and every Act-2 axis refuses to run unless the loaded
hash matches the one it declares. With `core.autocrlf=true` a fresh Windows
checkout rewrites 400 line endings: **8,414 → 8,814 bytes**, hash
`e2b8527010231a81fd31b6eeb9de3d8c` → `56413e34caf21bb7800b558b6062daae`. **The
language's identity depended on which OS cloned the repo.** Pinned in
`.gitattributes` as `-text`; the stored blob is already LF, so no blob and no
working copy changed.

⭐ **The lesson is one level past "simulate the target environment": check the
simulation is faithful, and when it disagrees with reality find out which one is
lying before believing either.** Re-run with `autocrlf=false`: 1520 passed /
6 skipped, matching the box's 1520 exactly plus the two new skips.

## R3 · `ssh()` returned `None` instead of output, silently

`subprocess.run(..., text=True)` decodes with the Windows locale codec, and every
log this project writes is full of `⛔`, `✅` and `═`. Under cp1252 the decode
raises **inside subprocess's reader thread**, where the exception is printed and
discarded, and `run` returns `stdout=None` with rc=2.

`poll` — the only window onto a box that is billing — died on it, and a
`check=False` caller would simply have carried on with `None`. Its sibling
`md5_remote` would have returned `None` as a checksum, which `verify_checksum`
refuses; **that path was covered by an unrelated guard being right, not by this
one.** Same family as the cp1252 `print` crash in `DECISIONS_2026_09_03.md` R5,
but on the input side and quiet instead of loud.

## R4 · The launch defaults had never matched reality

`launch` defaulted to `gpu_1x_a100` / `us-west-1`. Every run this project has
done was on `gpu_1x_a100_sxm4` in `us-west-2`
(`runs/act2/retrain12/INSTANCE.json`), and today the PCIe A100 had **no capacity
in any region** — so the default was not merely wrong, it was unlaunchable, and
it failed with a bare `HTTP 400` whose body (`insufficient-capacity`) was
discarded. ⭐ It matters past convenience: the 40 GiB wall the pipeline asserts
against and the 15,598 s/adapter reference are properties of *that card*.

## R6 · The corpus manifest was not in the persist set — and determinism saved it

The gate box persisted its weights, config, cell label, transcripts, run log and
adapter manifest. It did **not** persist `corpus_ct-s20624/manifest.json`, which
carries the corpus's own recipe lag profile — the comparison quantity for D5. The
box was `terminating` by the time that was noticed and the pull returned **0
bytes**.

⛔ And it wrote a 0-byte file, which is the s20620 shape in miniature: an empty
arrival and a file nobody asked for look identical afterwards. Deleted rather
than left to be found.

⭐⭐ **RECOVERED BY REBUILD, AND PROVEN.** The corpus was regenerated locally at
seed 20624 and its `train.jsonl` sha256 came back **`dd40e22f85b0b6e4`**, equal
to the value the box recorded in its persisted log. This is exactly what the
determinism fix (`2405a27`, R4 of the previous arc) was for: an artifact outside
the persist set was recovered by reconstruction and *verified* to be the same
one, rather than assumed to be.

⛔ **Still a gap.** Reconstruction only works because this corpus is
deterministic and its sha was written down. The persist set should include the
corpus manifest. Not yet fixed.

## R5b · The watcher watched nothing for an hour, and silence looked like health

**Claimed.** A monitor was armed on both boxes, emitting on stage transitions,
`FAILED`, `DONE`, stalls and self-termination.

**Actually.** Its log paths were relative to the repo, and a non-interactive ssh
lands in `$HOME`, not `~/tlon`. `grep` and `stat` matched nothing for sixty
minutes. Both boxes were in fact healthy — but the watcher could not have told
anyone otherwise.

⭐ **The only reason it surfaced is that the stall branch fires on
NOT-CHANGING rather than on bad news.** A monitor written to emit progress alone
would have been silent, and silent is indistinguishable from healthy. That is
the same argument the on-instance watchdog is built on, arriving from the other
direction.

⭐⭐ **THIS IS THE THIRD TIME TODAY THE SAME REMEDY APPLIED:** prove the path at
ARM TIME. `terminate_reachable()` does it for the kill path; the new provision
probe does it for the save path; the monitor now refuses to arm unless its log
is readable AND already contains stage lines. **A watcher that cannot see is
worse than no watcher, because it is the reason nobody looks.**

⛔ Also: a missing size is now reported as *"the watcher lost its instrument"*,
not as a stall. They are different facts and only one of them is about the box.

## R5 · The `tests` floor runs before the watchdog arms

`pipeline_solo_regen.sh` failed its `tests` stage — which is stage 2, and the
watchdog arms at stage 6. The box therefore sat **idle and billing with no
guard** until it was noticed by hand. Copied from `pipeline_asymmetric_recert.sh`,
which has no watchdog at all, so the ordering came in with the procedure.
⛔ **Not yet fixed.** Arming the watchdog before the floors would guard the idle
window; running the floors first is what keeps a broken tree from reaching the
GPU. Both are right and the ordering has to be decided rather than inherited.

---

## Open, and what closes it

| open | closes on |
|---|---|
| Does corpus lag-1 responsiveness reach the model? | the `ct-s20624` gate read, prereg `abde6124` |
| Are the eleven other adapters worth buying? | the same read |
| Two corpus lag-1 z figures wear one name: prereg §1 quotes **+120.36**, `runs/act2/retrain12_ct/corpus_ct-s20624/manifest.json` records **518.64** at 1445 chains | naming them by their build, not by the property |
| Watchdog-vs-floors ordering (R5) | a decision, not a discovery |
| Per-recipe rulers + `FLOOR_ka` recompute | the 84 transcripts landing |
| Amendment C (design → factorial) | after the rulers |
