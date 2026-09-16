"""⛔⛔ THE WATCHDOG'S ONE JOB, WHICH IT HAD NEVER ONCE PERFORMED.

`epochlevB-s20624`, 2026-09-16. The run finished. The watchdog noticed, flushed
the readings correctly, and then died:

    File "tools/act2_watchdog.py", line 234, in lambda_terminate
        or pathlib.Path("/etc/lambda-instance-id").read_text().strip())
    FileNotFoundError: [Errno 2] No such file or directory: '/etc/lambda-instance-id'

The box ran on, idle, for 4 h 49 m at $3.29/h. Every earlier run in this
campaign had been terminated by hand, so this path had never executed
successfully even once — the safety device was untested precisely because it was
never needed until it was.

⛔⛔ AND THERE WAS ALREADY A PREFLIGHT. `terminate_reachable()` ran at arm time,
exercised the credential, the network and the Cloudflare User-Agent, printed
"terminate path verified", and never touched the INSTANCE ID — the other input
`lambda_terminate` needs. A green check for the adjacent thing. That is the same
defect as the voided lag curve on the same run: the guard and the operation did
not travel the same path.

⭐ So these tests do not ask "is there a preflight". They ask: **does the
preflight fail in exactly the situations where the real terminate would fail?**
"""
from __future__ import annotations

import ast
import io
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import act2_watchdog as wd                                     # noqa: E402

OUR_IP = "209.20.157.154"
OUR_ID = "4b49e0a8d88f4a56b3696f0f9d375133"


def _no_local_id(monkeypatch, tmp_path, *, addrs="172.29.150.17 127.0.0.1"):
    """The box exactly as it actually was: no env var, and no id file.

    ⛔ Only the ONE path the resolver reads is redirected; the rest of pathlib
    keeps working. A blanket patch would make these tests pass for a reason
    unrelated to the bug.
    """
    import socket
    import subprocess

    monkeypatch.delenv("LAMBDA_INSTANCE_ID", raising=False)
    monkeypatch.setenv("LAMBDA_API_KEY", "not-a-real-key")
    missing = tmp_path / "definitely-not-here"
    orig = wd.pathlib.Path

    def fake_path(arg, *a, **k):
        if str(arg) == "/etc/lambda-instance-id":
            return orig(missing)
        return orig(arg, *a, **k)

    monkeypatch.setattr(wd.pathlib, "Path", fake_path)
    # ⛔ `subprocess` and `socket` are imported INSIDE the resolver, so they are
    # not attributes of the watchdog module — patch the real modules, which is
    # the same object the function-level import binds.
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: type("R", (), {"stdout": addrs})())
    monkeypatch.setattr(socket, "gethostbyname", lambda h: "127.0.0.1")


def test_the_PREFLIGHT_REFUSES_when_the_id_cannot_be_resolved(monkeypatch,
                                                              tmp_path):
    """⛔⛔ THE BUG ITSELF, AS THE PREFLIGHT SHOULD HAVE SEEN IT. No env var, no
    id file, and no running instance matching this box — the real terminate
    cannot name its target, so arming must be refused. The OLD preflight
    returned True here, which is how the box survived its own run."""
    _no_local_id(monkeypatch, tmp_path)
    monkeypatch.setattr(wd, "_lambda_get",
                        lambda path, key: [{"id": "someone-elses",
                                            "ip": "10.0.0.1",
                                            "private_ip": "172.16.0.1"}])
    ok, why = wd.terminate_reachable()
    assert ok is False, "the preflight passed on a box that cannot name itself"
    assert "resolve" in why.lower(), why


def test_the_RESOLVER_falls_back_to_the_API_when_the_box_knows_nothing(
        monkeypatch, tmp_path):
    """⭐ THE FIX. The API knows which instance holds this box's address even
    when the box has been told nothing about itself — so provisioning having
    gone wrong no longer costs a termination."""
    _no_local_id(monkeypatch, tmp_path)
    monkeypatch.setattr(wd, "_lambda_get",
                        lambda path, key: [{"id": "other", "ip": "10.0.0.1",
                                            "private_ip": "10.0.0.2"},
                                           {"id": OUR_ID, "ip": OUR_IP,
                                            "private_ip": "172.29.150.17"}])
    assert wd.resolve_instance_id("k") == OUR_ID


def test_the_PREFLIGHT_REFUSES_when_the_resolved_id_is_not_RUNNING(monkeypatch):
    """⛔ A terminate aimed at an id the API does not list is a silent no-op —
    it returns success and kills nothing, which is the most expensive kind of
    green."""
    monkeypatch.setenv("LAMBDA_API_KEY", "k")
    monkeypatch.setenv("LAMBDA_INSTANCE_ID", "a-stale-id")
    monkeypatch.setattr(wd, "_lambda_get",
                        lambda path, key: [{"id": OUR_ID, "ip": OUR_IP}])
    ok, why = wd.terminate_reachable()
    assert ok is False and "no-op" in why, why


def test_the_PREFLIGHT_PASSES_when_the_id_resolves_AND_is_live(monkeypatch):
    """⭐ The control. A guard that cannot pass is an outage, and every refusal
    above is only meaningful against it."""
    monkeypatch.setenv("LAMBDA_API_KEY", "k")
    monkeypatch.setenv("LAMBDA_INSTANCE_ID", OUR_ID)
    monkeypatch.setattr(wd, "_lambda_get",
                        lambda path, key: [{"id": OUR_ID, "ip": OUR_IP}])
    ok, why = wd.terminate_reachable()
    assert ok is True, why
    assert OUR_ID in why, "the preflight does not say WHICH instance it verified"


def test_the_PREFLIGHT_REFUSES_when_the_API_is_unreachable(monkeypatch):
    """⛔ The original reason this preflight exists — Cloudflare 403s a missing
    User-Agent with code 1010, which reads exactly like an auth failure."""
    monkeypatch.setenv("LAMBDA_API_KEY", "k")

    def boom(path, key):
        raise OSError("connection refused")

    monkeypatch.setattr(wd, "_lambda_get", boom)
    ok, why = wd.terminate_reachable()
    assert ok is False and "unreachable" in why


# ── the structural guard: one resolver, both paths ─────────────────────────

def _func(name):
    tree = ast.parse(io.open(ROOT / "tools" / "act2_watchdog.py",
                             encoding="utf-8-sig").read())
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError("%s not found — the guard below would be vacuous" % name)


def _calls(fn):
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


@pytest.mark.parametrize("fn_name", ["lambda_terminate", "terminate_reachable"])
def test_BOTH_paths_resolve_the_id_THE_SAME_WAY(fn_name):
    """⭐⭐ THE LESSON, ASSERTED STRUCTURALLY. The preflight was useless because
    it checked a DIFFERENT set of preconditions than the operation it certified.
    Whatever route the terminate takes to an instance id, the preflight must
    take the same one — so both are required to call the one resolver, and
    neither may read the id itself."""
    fn = _func(fn_name)
    calls = _calls(fn)
    assert "resolve_instance_id" in calls, (
        "%s does not call resolve_instance_id — the preflight and the terminate "
        "can now disagree about whether an id exists, which is exactly how "
        "'terminate path verified' preceded a FileNotFoundError" % fn_name)
    # ⛔⛔ THE CODE'S STRING CONSTANTS, NOT `ast.dump`. My first spelling of this
    # assertion dumped the whole node and searched the text — which includes the
    # DOCSTRING, and the docstring names `/etc/lambda-instance-id` while
    # explaining why reading it was the bug. The guard failed on its own
    # explanation. That is `grep_a_rendering` inside the test written to close
    # that very class, which is worth the extra six lines to not repeat.
    body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                           and isinstance(fn.body[0].value, ast.Constant)
                           and isinstance(fn.body[0].value.value, str)) else fn.body
    literals = {n.value for stmt in body for n in ast.walk(stmt)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert not any("lambda-instance-id" in s for s in literals), (
        "%s reads the id file directly again; that path is one of THREE the "
        "resolver tries, and hardcoding it is the original bug" % fn_name)


def test_the_resolver_tries_the_API_and_not_only_the_local_sources():
    """⛔⛔ A resolver that only reads local state reproduces the failure with
    more steps. The API route is the one that works on a box that was told
    nothing about itself, so its absence is a regression."""
    fn = _func("resolve_instance_id")
    calls = _calls(fn)
    assert "_lambda_get" in calls, (
        "resolve_instance_id no longer asks the API which instance this is — "
        "on a box with no env var and no id file it can only fail")
