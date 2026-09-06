# ═══ THE SAFETY SCAFFOLDING EVERY SELF-TERMINATING PIPELINE SHARES ═════════
#
# ⛔⛔ THIS FILE EXISTS SO THE SAFETY LOGIC CANNOT DRIFT. Three pipelines run on
# boxes that terminate themselves, and each one needs the same four things: a
# failure handler that survives an early exit, a log that never appends to
# another run's record, a watchdog armed BEFORE any GPU time, and a `~/DONE`
# that means PERSISTED rather than COMPUTED. Both losses on 2026-09-04 were in
# that logic. Copied into each script, the next fix lands in one copy and not
# the others — and the box running the expensive job is the one that keeps the
# stale copy.
#
# ⭐ SOURCED, NOT TEMPLATED. The stage SEQUENCES genuinely differ (the LoRA arm
# trains six adapters with solo transcripts; the full-weight arm trains one
# object with an epoch-1 read and no transcripts at persist time), so those live
# in separate scripts. Only the scaffolding is shared, and it is shared by being
# one copy rather than by being similar.
#
#   source "$(dirname "$0")/pipeline_lib.sh"
#   tlon_trap_init
#   tlon_log_init "$ROOT" pipeline_x.log
#   ... floors ...
#   tlon_arm_watchdog ...
#   ... work ...
#   tlon_gate_done ...

# ── 1 · THE FAILURE HANDLER ─────────────────────────────────────────────────
tlon_trap_init() {
  # ⛔ THE TRAP IS ARMED BEFORE $STAGE/$LOG EXIST, so it must not depend on them.
  # Under `set -u` a bare $STAGE here makes the handler ITSELF fail on any early
  # exit — and the handler is the only thing that reports why the run stopped,
  # so its failure erases the diagnosis exactly when there is one.
  trap 'rc=$?; if [ $rc -ne 0 ]; then
          echo "⛔ FAILED at stage: ${STAGE:-<before init>} (rc=$rc)" | tee -a "${LOG:-/dev/null}"
          echo "${STAGE:-<before init>} rc=$rc" > ~/FAILED
        fi' EXIT
}

# ── 2 · THE LOG, AND WHY IT ROTATES ─────────────────────────────────────────
tlon_log_init() {
  # $1 = run root   $2 = log basename
  local root="$1" name="$2"
  mkdir -p "$root/logs"
  LOG="$root/$name"
  # ⛔⛔ NEVER APPEND TO ANOTHER RUN'S LOG. Some run logs are committed, so a
  # fresh clone arrives holding a previous run's file and every `tee -a` writes
  # into it. The gate box did exactly that on 2026-09-04: its log opened with a
  # stage line from the run that DIED, an hour before that box existed. Nothing
  # is lost, but two runs share one record and a reader can attribute one run's
  # numbers to the other — caveat decay with the caveat simply absent.
  # ⭐ Rotate rather than delete: the old record is still somebody's evidence.
  if [ -s "$LOG" ]; then
    local prev="$LOG.$(date -u +%Y%m%dT%H%M%SZ).prev"
    mv "$LOG" "$prev"
    echo "⚠ an earlier log was already here; moved it to $prev"
  fi
  STAGE=init
  T_START=$(date +%s)
}

step() { STAGE="$1"; echo "=== [$1] $(date -u +%H:%M:%S) ===" | tee -a "$LOG"; }

# ── 3 · THE WATCHDOG, ARMED BEFORE ANY GPU TIME ─────────────────────────────
tlon_arm_watchdog() {
  # $1 py  $2 root  $3 hf_repo  $4 marker  $5 deadline_h  $6 stall_min  $7 watched_pid
  local py="$1" root="$2" repo="$3" marker="$4" dl="$5" stall="$6" watched="$7"
  rm -f ~/DONE ~/FAILED
  # ⛔⛔ --flush-cmd IS THE KILL PATH'S LAST WORDS. A box terminated for a stall
  # or a dead process still holds its run log — the record of WHY, and the one
  # artifact re-running cannot regenerate. `retrain12/pipeline_retrain.log` was
  # lost exactly that way. Best-effort, and it can never block the terminate:
  # this fires on a box already burning money for nothing.
  nohup "$py" tools/act2_watchdog.py \
        --pid "$watched" --marker "$marker" \
        --log "$LOG" --done "$HOME/DONE" \
        --deadline-h "$dl" --stall-min "$stall" --poll-s 300 \
        --flush-cmd "$py tools/act2_box_persist.py --root $root --repo $repo flush" \
        > "$root/watchdog.log" 2>&1 &
  WD=$!
  sleep 5
  # ⛔⛔ PROBED, NOT ASSUMED. A watchdog that died on arming leaves a run
  # unguarded while every log line says it is guarded — `assert_the_mutation`
  # applied to the one process whose whole job is to act when nothing else can.
  kill -0 "$WD" 2>/dev/null || {
    echo "⛔⛔ WATCHDOG DIED ON ARMING — refusing to run unguarded" | tee -a "$LOG"
    cat "$root/watchdog.log" | tee -a "$LOG"
    exit 1
  }
  echo "  ✅ watchdog armed, pid $WD, watching $watched" | tee -a "$LOG"
}

# ── 4 · THE GATE ON ~/DONE ──────────────────────────────────────────────────
tlon_persist_run_files() {
  # $1 py  $2 root  $3 hf_repo  $4.. run-level files (the log is always added)
  local py="$1" root="$2" repo="$3"; shift 3
  step persist_run
  # ⛔ Run-level artifacts are not regenerable by re-running, because what they
  # record is THIS run.
  local f
  for f in "$@"; do
    "$py" tools/act2_box_persist.py --root "$root" --repo "$repo" \
        file --path "$f" --subdir "$(basename "$root")" 2>&1 | tee -a "$LOG"
  done
  "$py" tools/act2_box_persist.py --root "$root" --repo "$repo" \
      file --path "$LOG" --subdir "$(basename "$root")" 2>&1 | tee -a "$LOG"
}

tlon_verify_cells() {
  # $1 py  $2 root  $3 hf_repo  $4 cells
  local py="$1" root="$2" repo="$3" cells="$4"
  step verify_persisted
  # ⛔⛔ THE GATE ON ~/DONE. The watchdog terminates within one poll of seeing
  # that marker — correctly, because a finished run that keeps billing is pure
  # waste. So the marker must mean PERSISTED, not COMPUTED. Until this exits 0
  # the run's output exists only on a box that is trying to end itself.
  "$py" tools/act2_box_persist.py --root "$root" --repo "$repo" \
      verify --cells "$cells" 2>&1 | tee -a "$LOG"
}

tlon_mark_done() {
  # $1 repo  $2 what was certified (free text for the log)
  #
  # ⛔⛔ THE ONLY PLACE THE THREE LIVE PIPELINES WRITE ~/DONE. The marker means
  # PERSISTED-AND-VERIFIED, and the watchdog terminates within one poll of
  # seeing it — so a pipeline that touches it itself has quietly made every
  # verify above advisory. `pipeline_solo_regen.sh` verifies something different
  # from the other two (tarball run-files, not cells), which is exactly why the
  # marker is factored out from the verification rather than bundled with one
  # spelling of it: the check varies, the meaning of the marker must not.
  #
  # ⚠️ NOT "the only place in the repository", and the difference is recorded
  # rather than smoothed over: six OLDER pipelines still write the marker
  # themselves (asymmetric_recert, drift, ki_target, multiturn,
  # positive_control, recipe_variance, variance_decompose). They are historical
  # one-shots that already ran, and converting them is a re-verification nobody
  # has paid for. `tests/test_pipeline_lib.py` PINS that list, so the debt is
  # visible and cannot quietly grow by one more script.
  local repo="$1" what="$2"
  step done
  [ -n "${TLON_SUMMARY:-}" ] && echo "${TLON_SUMMARY}" | tee -a "$LOG"
  echo "  certified: $what" | tee -a "$LOG"
  echo "  everything above is in hf://$repo and hub-verified. The local" | tee -a "$LOG"
  echo "  collect is now a convenience, not the only path off this box." | tee -a "$LOG"
  echo "  total wall: $(( $(date +%s) - T_START )) s" | tee -a "$LOG"
  touch ~/DONE
}

tlon_gate_done() {
  # The common path: persist run files, verify CELLS, mark done.
  # $1 py  $2 root  $3 hf_repo  $4 cells  $5.. extra run files
  local py="$1" root="$2" repo="$3" cells="$4"; shift 4
  tlon_persist_run_files "$py" "$root" "$repo" "$@"
  tlon_verify_cells "$py" "$root" "$repo" "$cells"
  tlon_mark_done "$repo" "$cells"
}

