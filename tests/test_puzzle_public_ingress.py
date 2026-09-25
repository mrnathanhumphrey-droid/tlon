"""⛔⛔ THE ORACLE'S TWO TRAPS, BOTH OF WHICH LOOK HEALTHY WHEN WRONG.

`D:\\SportsThought` is reached only through a Cloudflare Tunnel: its `fly.toml`
declares no `[http_service]` and asks for no public IP, and its entrypoint binds
`--host 127.0.0.1`. Both are correct there and fatal here. An app with either
one deploys green, passes its own in-machine health check, logs "Uvicorn
running", and cannot be reached by anybody on the internet.

⭐ THE POINT OF TESTING IT HERE: that failure is indistinguishable from success
in every log line the deploy produces. The only cheap place to catch it is
before the deploy.

⛔ THE BIND TEST RUNS THE SCRIPT; IT DOES NOT GREP IT. A test that searched the
entrypoint for the string "0.0.0.0" would pass on a file where the string sits
in a comment — and this repo has already shipped that bug twice, once against a
guard's own explanatory prose. So the loopback refusal is executed.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FLY = ROOT / "puzzle" / "fly.toml"
ENTRY = ROOT / "puzzle" / "docker-entrypoint.sh"

try:
    import tomllib
except ModuleNotFoundError:                      # pragma: no cover
    tomllib = None


def _working_bash() -> str | None:
    """A bash that actually runs a script, not just a name on PATH.

    ⛔ `shutil.which("bash")` IS NOT ENOUGH ON WINDOWS. It finds the WSL
    launcher stub, which exits non-zero with an empty stderr and UTF-16 noise
    on stdout when no distribution is installed. A test asserting only
    `returncode != 0` would have PASSED against that stub — green, and having
    executed nothing. The probe below is what separates "bash refused our
    script" from "bash never ran".

    ⛔⛔ AND THE PROBE RUNS A SCRIPT AT A REAL PATH, NOT `bash -c`. The first
    version probed with `-c "echo ok"`, which WSL's bash passes — and then WSL
    cannot open `D:\\Tlon\\puzzle\\docker-entrypoint.sh` because it wants
    `/mnt/d/...`, so the real test failed with an empty stderr that looked
    exactly like our guard not firing. Simulate the target environment, then
    check the simulation is faithful: the capability needed is "runs THIS
    script at THIS path", so that is what is probed.
    """
    import tempfile

    # ⭐ Git's bash first — it understands Windows paths. WSL's launcher is last
    # because it is the one that produces the convincing-looking false result.
    cands = [r"C:\Program Files\Git\bin\bash.exe",
             r"C:\Program Files\Git\usr\bin\bash.exe",
             shutil.which("bash")]
    with tempfile.TemporaryDirectory() as td:
        probe_sh = pathlib.Path(td) / "probe.sh"
        probe_sh.write_text("#!/usr/bin/env bash\necho tlon_ok\n",
                            encoding="utf-8", newline="\n")
        for exe in cands:
            if not exe or not pathlib.Path(exe).exists():
                continue
            try:
                probe = subprocess.run([exe, str(probe_sh)],
                                       capture_output=True, text=True, timeout=20)
            except OSError:
                continue
            if probe.returncode == 0 and "tlon_ok" in (probe.stdout or ""):
                return exe
    return None


BASH = _working_bash()


@pytest.fixture(scope="module")
def fly() -> dict:
    if tomllib is None:
        pytest.skip("tomllib needs python 3.11+")
    # ⛔ PARSE THE ARTEFACT, DO NOT GREP IT. `[http_service]` appearing anywhere
    # in the bytes includes it appearing inside the comment that explains why it
    # must be there — which is exactly the shape that fails CLOSED on correct
    # evidence and OPEN on a commented-out section.
    return tomllib.loads(FLY.read_text(encoding="utf-8"))


def test_fly_declares_a_public_http_service(fly):
    assert "http_service" in fly, (
        "⛔⛔ no [http_service] — this is the Oracle's tunnel-only shape and "
        "the app would deploy clean and be unreachable")
    assert fly["http_service"]["internal_port"] == 8080
    assert fly["http_service"]["force_https"] is True


def test_fly_scales_to_zero(fly):
    """⭐ A GPU machine left running is the largest standing cost in the
    project, and it bills whether or not anybody types."""
    svc = fly["http_service"]
    assert svc["min_machines_running"] == 0
    assert svc["auto_start_machines"] is True
    assert svc["auto_stop_machines"] in ("suspend", "stop", True)


def test_fly_keeps_exactly_one_machine_worth_of_state(fly):
    """⛔ The bench is a SQLite file on a volume. Two machines would not share
    it, so a reader's conversation would vanish whenever the load balancer
    moved them — data loss that looks like a UI bug."""
    mounts = fly.get("mounts", [])
    assert mounts, "⛔ no volume — the bench and the 14 GB base model need one"
    assert mounts[0]["destination"] == "/data"


def test_a_cold_model_load_cannot_boot_loop_the_machine(fly):
    """⛔⛤ THIS TEST USED TO ASSERT `grace_period >= 120s`, AND BOTH HALVES OF
    THAT WERE WRONG.

    It encoded the belief that a long grace period was the fix for a slow cold
    start. Two things refute it:

      * FLY WILL NOT HONOUR IT. An http_service check's grace is capped at 60
        seconds. The deploy lowers the value and mentions it once, in passing,
        among the build output — so the config read as protective while the
        platform ignored it, and the suite agreed with the config rather than
        with the machine.
      * NO GRACE PERIOD IS LONG ENOUGH ANYWAY. A cold machine pulls ~14 GB of
        base weights onto the volume before `load()` starts.

    ⭐ The actual fix is that `server._startup` warms the speaker on a THREAD,
    so uvicorn binds immediately and `/healthz` answers while the card warms.
    That is asserted by `test_the_speaker_is_warmed_off_the_startup_path`; this
    one now only checks the config does not claim a grace it will not get.
    """
    grace = fly["http_service"]["checks"][0]["grace_period"]
    assert grace.endswith("s")
    assert int(grace[:-1]) <= 60, (
        "grace %s will be silently lowered to 60s by Fly — write what is "
        "enforced" % grace)


# ── the bind ────────────────────────────────────────────────────────────────

@pytest.mark.skipif(BASH is None, reason="no working bash on this box")
def test_entrypoint_refuses_to_bind_loopback():
    """⛔⛔ RUN, DON'T READ. This executes the guard with the exact value that
    broke the Oracle and asserts the process dies."""
    proc = subprocess.run(
        [BASH, str(ENTRY)],
        env={"TLON_HOST": "127.0.0.1", "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, timeout=30)
    assert proc.returncode != 0, (
        "⛔⛔ the entrypoint accepted a loopback bind — this is the Oracle's "
        "trap and it produces an app nothing can reach")
    assert "REFUSING TO START" in proc.stderr


@pytest.mark.skipif(BASH is None, reason="no working bash on this box")
def test_entrypoint_refuses_localhost_too():
    """⭐ The same mistake spelled the other way. A guard that only knew the
    dotted form would wave `localhost` straight through."""
    proc = subprocess.run(
        [BASH, str(ENTRY)],
        env={"TLON_HOST": "localhost", "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, timeout=30)
    assert proc.returncode != 0
    assert "REFUSING TO START" in proc.stderr


def test_dockerfile_bakes_the_adapter():
    """⛔ A machine that boots without the adapter serves the UNTUNED BASE,
    which scored 0.0% on write. It would answer in English, return 200s, and
    look entirely healthy to every check in this file.

    ⛔⛤ THIS ASSERTED `ct-s20624` BY NAME and went red when v1 became
    `dosed-s20624` — red for a STALE REASON, guarding a cell rather than the
    property it cares about, which is that SOME adapter is baked and named. The
    identity of v1 belongs to `test_puzzle_serves_v1.py`, which owns the
    constant and checks the COPY and the ENV agree; duplicating the literal
    here would mean the next swap has to be made correctly in two places or a
    green suite would disagree with itself.
    """
    body = ENTRY.parent.joinpath("Dockerfile").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.lstrip().startswith("#"))
    assert "COPY runs/puzzle_speaker/" in code, (
        "no adapter is baked into the image at all")
    assert "TLON_ADAPTER=" in code


# ── the card ────────────────────────────────────────────────────────────────

def test_fly_asks_for_a_gpu(fly):
    """⛔⛔ WITHOUT `gpu_kind` FLY HANDS BACK A CPU MACHINE.

    This serves Qwen2.5-7B with a LoRA. On CPU torch still runs — every turn
    just takes roughly a minute. Slow, not broken: the container boots, the
    health check passes, `/healthz` is green, and the only symptom is that the
    bench feels dead. The Dockerfile names the same failure for the same
    reason, and it is the exact shape of every other defect this file guards.

    ⭐ It is also the single largest cost line in the project, which is why
    `min_machines_running = 0` sits above — a card that bills while nobody is
    typing is the other way this goes wrong.
    """
    vm = fly.get("vm")
    assert vm, "⛔⛔ no [[vm]] block — Fly would pick a default CPU machine"
    assert vm[0].get("gpu_kind"), (
        "⛔⛔ no gpu_kind — this deploys a 7B onto a CPU and it will look "
        "healthy while taking a minute a turn")
    assert vm[0].get("gpus", 0) >= 1


def test_the_host_has_room_to_load_the_shards(fly):
    """⛔ The weights are loaded and quantised on the HOST before they reach the
    card. 8 GB was the value set before anything had tried it."""
    mem = fly["vm"][0].get("memory", "")
    assert mem.endswith("gb") and int(mem[:-2]) >= 16, (
        "host memory %r is too small to stage a 7B's shards" % mem)


def test_the_puzzle_does_not_quietly_drop_to_the_frozen_lexicon(fly):
    """⭐ Belt and braces with `test_puzzle_serves_the_trained_lexicon`, which
    owns this. Named here too because THIS file is what someone reads when they
    are about to deploy."""
    assert fly["env"]["TLON_LEXICON"] == "lexicon_expanded.yaml"


# ── the challenge ───────────────────────────────────────────────────────────

def test_fly_carries_a_turnstile_sitekey(fly):
    """⛔ An empty sitekey renders no widget, so every reader would arrive with
    no token and `/say` would refuse all of them — a puzzle that looks live and
    answers nobody. The SITE key is public by design; it is config, not a
    secret, and it belongs here where a deploy can see it."""
    key = fly["env"].get("TLON_TURNSTILE_SITEKEY", "")
    assert key, "⛔⛔ no TLON_TURNSTILE_SITEKEY — the widget cannot render"
    assert key.startswith("0x"), (
        "⛔ %r is not shaped like a Turnstile sitekey" % key)


def test_fly_does_NOT_carry_the_turnstile_secret(fly):
    """⛔⛔ THE SECRET LIVES ONLY IN `fly secrets`, NEVER IN THE REPO.
    `fly.toml` is committed; anything in its `[env]` is public to everyone who
    can read the repository. A secret here would be a secret no longer, and the
    widget would have to be rebuilt to rotate it."""
    body = FLY.read_text(encoding="utf-8")
    assert "TURNSTILE_SECRET_KEY" not in fly["env"], (
        "⛔⛔ the Turnstile SECRET is in fly.toml's [env] — it is committed")
    # the name may appear in prose explaining where it does live
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.lstrip().startswith("#"))
    assert "TURNSTILE_SECRET_KEY" not in code


# ── the cold start ──────────────────────────────────────────────────────────

def test_the_speaker_is_warmed_off_the_startup_path():
    """⛔⛔ A BLOCKING STARTUP IS A BOOT LOOP ON THIS PLATFORM.

    FastAPI accepts no connection until the startup handler returns, and a cold
    machine pulls ~14 GB of base weights onto the volume before `load()` even
    begins. Fly caps an http_service check's grace period at 60s — it lowers
    the config's value and says so only in passing at deploy time — so a
    synchronous load fails the check, the machine restarts, and the download
    starts over. Every log line would read "health check failed".
    """
    import ast

    src = (ROOT / "puzzle" / "server.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_startup"), None)
    assert fn, "no _startup handler"

    spawns = {getattr(c.func, "attr", None) for c in ast.walk(fn)
              if isinstance(c, ast.Call)}
    assert "Thread" in spawns, (
        "⛔⛔ _startup loads the speaker synchronously — the machine will fail "
        "its health check before a cold model load finishes")

    # ⭐ and the Turnstile preflight must stay SYNCHRONOUS: it is the one thing
    # that should stop the boot.
    body_calls = [c for c in fn.body if isinstance(c, ast.Expr)
                  and isinstance(c.value, ast.Call)]
    first = body_calls[0].value if body_calls else None
    assert first is not None and getattr(first.func, "attr", "") == "preflight", (
        "⛔ TS.preflight() is no longer the first thing startup does")


def test_the_grace_period_is_one_fly_will_honour(fly):
    """⛔ Fly lowers anything over 60s on an http_service check. A config asking
    for more is a config that lies to whoever reads it next."""
    grace = fly["http_service"]["checks"][0]["grace_period"]
    assert grace.endswith("s") and int(grace[:-1]) <= 60
