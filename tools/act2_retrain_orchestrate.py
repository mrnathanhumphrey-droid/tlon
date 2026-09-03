"""⛔⛔ THE ORCHESTRATOR — launch, provision, train, VERIFIED collect, PERSIST,
then and only then terminate.

    python tools/act2_retrain_orchestrate.py launch
    python tools/act2_retrain_orchestrate.py provision --host <IP>
    python tools/act2_retrain_orchestrate.py train     --host <IP>
    python tools/act2_retrain_orchestrate.py collect   --host <IP>
    python tools/act2_retrain_orchestrate.py persist
    python tools/act2_retrain_orchestrate.py terminate --instance <ID>

⭐ SUBCOMMANDS, NOT ONE BUTTON. Each stage is separately runnable and separately
inspectable, because the failure that started this was a single unverified
step inside a larger motion that nobody watched.

⛔⛔ THE ONLY PATH TO TERMINATION RUNS THROUGH `act2_provision.terminate`, which
calls `may_terminate` and raises unless EVERY adapter is (a) present locally,
(b) md5-identical to the checksum computed ON THE BOX before the pull, and
(c) in durable storage. `s20620` failed all three and nothing noticed, because
nothing asked.

⛔ `LAMBDA_API_KEY` and `HF_TOKEN` are read from the environment / the env file
and are never logged.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from act2_provision import (TransferError, launch, instances,  # noqa: E402
                            md5_local, push_durable, ssh, terminate,
                            verify_checksum, verify_pulled_set)

REPO_GIT = "https://github.com/mrnathanhumphrey-droid/tlon.git"
HF_REPO = "keyzersoze04/tlon-act2-adapters"
KEY = pathlib.Path.home() / ".ssh" / "tlon"
REMOTE_ROOT = "~/tlon/runs/act2/retrain12"
LOCAL_ROOT = pathlib.Path("runs/act2/retrain12")
NEW = ("s20624", "s20625", "s20626", "s20627", "s20628", "s20629")


def plan_collection(manifest: dict, local_root) -> list[dict]:
    """-> ledger records, from the BOX-SIDE manifest. Pure; unit-tested.

    ⛔ The expected set comes from the manifest the box wrote, not from a list
    typed here — otherwise a build that silently failed to train would simply be
    absent from both sides and agree.
    """
    root = pathlib.Path(local_root)
    out = []
    for name, m in sorted(manifest.items()):
        f = root / ("adapter_%s" % name) / "adapter_model.safetensors"
        out.append({"name": name,
                    "box_md5": m.get("md5"),
                    "local_md5": md5_local(f) if f.exists() else None,
                    "local_path": str(f),
                    "remote_path": m.get("remote_path"),
                    "bytes": m.get("bytes"),
                    "durable_uri": None})
    return out


def _run(cmd, **kw):
    print("  $ %s" % " ".join(cmd[:6]), flush=True)
    return subprocess.run(cmd, check=True, **kw)


def cmd_launch(a):
    r = launch(instance_type=a.instance_type, region=a.region,
               ssh_key_name=a.ssh_key, name="tlon-retrain12")
    print(json.dumps(r, indent=2))
    print("\n⛔ RECORD THE INSTANCE ID. Nothing else can terminate it for you.")
    return 0


def cmd_status(_a):
    print(json.dumps(instances(), indent=2))
    return 0


def cmd_provision(a):
    """Clone at a PINNED commit and build the venv. ⛔ Not `git pull` — the box
    must run the code this run was designed against, not whatever main is."""
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    print("pinning the box to %s" % sha)
    ssh(a.host, KEY, "rm -rf ~/tlon && git clone -q %s ~/tlon" % REPO_GIT)
    ssh(a.host, KEY, "cd ~/tlon && git checkout -q %s" % sha)
    got = ssh(a.host, KEY, "cd ~/tlon && git rev-parse HEAD")
    if got != sha:
        raise TransferError("box is at %s, expected %s — refusing to train "
                            "against code this run was not designed against"
                            % (got, sha))
    print("  ✅ box pinned at %s" % got)
    # ⛔⛔ PINNED, AND THE PIN IS THE RUNBOOK'S. Installing "latest" pulled
    # torch 2.14.0+cu130 against a 12.8 driver, and `torch.cuda.is_available()`
    # came back False — the pipeline would have trained on CPU for forty hours.
    # RUNBOOK §5 records the exact versions the code demonstrably ran on and
    # that the cu128 index is REQUIRED. Environment drift is not a detail.
    ssh(a.host, KEY,
        "python3 -m venv ~/venv && ~/venv/bin/pip -q install -U pip && "
        "~/venv/bin/pip -q install --index-url https://download.pytorch.org/whl/cu128 "
        "torch==2.11.0 && "
        "~/venv/bin/pip -q install transformers==5.8.1 peft==0.19.1 "
        "datasets==4.8.5 numpy==2.2.6 jinja2==3.1.6 accelerate "
        "huggingface_hub scipy pytest")
    print("  ✅ venv built (runbook-pinned, cu128)")

    # ⛔⛔ REFUSE, DO NOT PRINT. A box whose torch cannot see the GPU will train
    # on CPU without erroring — slowly, expensively, and to completion.
    probe = ssh(a.host, KEY, "~/venv/bin/python -c "
                             "'import torch;print(torch.__version__, "
                             "torch.cuda.is_available(), torch.version.cuda)'")
    print("  torch probe: %s" % probe)
    if "True" not in probe.split():
        raise TransferError(
            "CUDA IS NOT AVAILABLE on the box (%s). Refusing to hand off to "
            "training — it would run on CPU to completion and bill for it. "
            "Check the driver against the wheel's CUDA version." % probe)
    print("  ✅ CUDA verified available")
    return 0


def cmd_env(a):
    """Put the credentials the ON-INSTANCE watchdog needs onto the box.

    ⛔⛔ A SELF-TERMINATING WATCHDOG NEEDS A CREDENTIAL THAT CAN TERMINATE. There
    is no narrower Lambda key, so this one can terminate any instance on the
    account — including other projects'. That is a real exposure and the reason
    it is written 0600, to a file, on a box that is itself terminated at the end
    of the run. The alternative is a watchdog that cannot fire, which is what
    the previous arrangement had and what it cost.

    ⛔ Shipped over STDIN, never on the command line: argv is visible in the
    remote process list and lands in shell history.
    """
    import os
    import re
    key = os.environ.get("LAMBDA_API_KEY")
    if not key:
        raise TransferError("LAMBDA_API_KEY is not set locally")
    hf = ""
    envf = pathlib.Path(r"D:\physics_detector\.env")
    if envf.exists():
        m = re.search(r"^HF_TOKEN=(.+)$",
                      envf.read_text(encoding="utf-8", errors="replace"), re.M)
        hf = m.group(1).strip().strip('"').strip("'") if m else ""
    body = "\n".join(("export LAMBDA_API_KEY=%s" % key,
                      "export LAMBDA_INSTANCE_ID=%s" % a.instance,
                      "export HF_TOKEN=%s" % hf, ""))
    # ⛔⛔ BYTES, NOT `text=True`. On Windows, text mode translates "\n" to
    # "\r\n" on the way into the pipe, so every exported value arrives with a
    # trailing carriage return. The file then has the right line count and the
    # right permissions and every value is one character wrong — an invalid HTTP
    # header, and the watchdog cannot terminate. Caught by a LENGTH check (89 on
    # the box against 88 locally); the shape check passed happily.
    subprocess.run(["ssh", "-i", str(KEY), "ubuntu@%s" % a.host,
                    "cat > ~/.tlon_env && chmod 600 ~/.tlon_env"],
                   input=body.encode("utf-8"), check=True)
    # ⛔ Verify by SHAPE and LENGTH, never by echoing the values back. Shape
    # alone cannot see a value that is right except for one invisible byte.
    n = ssh(a.host, KEY, ". ~/.tlon_env && echo ${#LAMBDA_API_KEY}")
    if n.strip() != str(len(key)):
        raise TransferError("the key arrived %s bytes long, sent %d — the "
                            "transfer altered it" % (n.strip(), len(key)))
    print("  ✅ key length matches (%s bytes)" % n.strip())
    out = ssh(a.host, KEY, "wc -l < ~/.tlon_env; stat -c %a ~/.tlon_env")
    print("  ✅ ~/.tlon_env written (%s) — 3 vars, perms 0600 expected"
          % " / ".join(out.split()))
    probe = ssh(a.host, KEY,
                ". ~/.tlon_env && cd ~/tlon && ~/venv/bin/python -c "
                "'import sys;sys.path.insert(0,\"tools\");"
                "from act2_watchdog import terminate_reachable;"
                "print(terminate_reachable())'")
    print("  watchdog kill-path from the box: %s" % probe)
    if "True" not in probe:
        raise TransferError("the watchdog cannot reach the terminate API FROM "
                            "THE BOX — it would refuse to arm, and the pipeline "
                            "would halt. Fix before training.")
    print("  ✅ the box can terminate itself")
    return 0


def cmd_train(a):
    # ⛔⛔ THE RECIPE IS PASSED EXPLICITLY AND THE PIPELINE REQUIRES IT. There is
    # no default on either side: a batch filed into an arm nobody chose is an
    # adapter in no cell of the factorial, and the matrix is rebuilt from
    # exactly these labels once the scrollback is gone.
    if a.recipe not in ("content-free", "content-transient"):
        raise TransferError("unknown --recipe %r" % (a.recipe,))
    env = "RECIPE=%s" % a.recipe
    if a.seeds:
        # ⭐ A GATE RUN trains ONE adapter to test an assumption before the
        # batch is bought. The pipeline's full seed literal is untouched.
        env += " SEEDS='%s'" % a.seeds
        print("  ⭐ SINGLE-SEED GATE RUN: seeds=%s" % a.seeds)
    # ⛔ Sources the credential file so the watchdog it spawns inherits the
    # key it needs. A non-interactive ssh does NOT read ~/.bashrc.
    ssh(a.host, KEY,
        "cd ~/tlon && . ~/.tlon_env && %s nohup bash tools/pipeline_retrain.sh "
        "> ~/retrain_stdout.log 2>&1 &" % env)
    print("  recipe=%s" % a.recipe)
    print("  ✅ pipeline launched under nohup; the on-instance watchdog arms "
          "itself in stage 3")
    print("  poll with: %s status --host %s" % (sys.argv[0], a.host))
    return 0


def cmd_poll(a):
    print(ssh(a.host, KEY,
              "tail -5 %s/pipeline_retrain.log 2>/dev/null; "
              "echo ---; ls ~/DONE ~/FAILED 2>/dev/null" % REMOTE_ROOT,
              check=False))
    return 0


def cmd_collect(a):
    """⛔⛔ THE STAGE WHOSE ABSENCE LOST s20620."""
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    raw = ssh(a.host, KEY, "cat %s/manifest.json" % REMOTE_ROOT)
    manifest = json.loads(raw)
    print("box manifest lists %d adapters" % len(manifest))

    for name in manifest:
        dest = LOCAL_ROOT / ("adapter_%s" % name)
        dest.mkdir(parents=True, exist_ok=True)
        _run(["scp", "-i", str(KEY), "-q",
              "ubuntu@%s:%s/adapter_%s/adapter_model.safetensors" % (a.host, REMOTE_ROOT, name),
              "ubuntu@%s:%s/adapter_%s/adapter_config.json" % (a.host, REMOTE_ROOT, name),
              str(dest)])
    _run(["scp", "-i", str(KEY), "-q", "-r",
          "ubuntu@%s:%s/logs" % (a.host, REMOTE_ROOT), str(LOCAL_ROOT)])
    _run(["scp", "-i", str(KEY), "-q",
          "ubuntu@%s:%s/pipeline_retrain.log" % (a.host, REMOTE_ROOT),
          str(LOCAL_ROOT)])

    records = plan_collection(manifest, LOCAL_ROOT)
    # ⛔ SET first, then per-artifact checksum. An empty pull passes every
    # per-file check trivially, because there are no files to check.
    verify_pulled_set(expected=list(manifest),
                      found=[r["name"] for r in records if r["local_md5"]])
    for r in records:
        verify_checksum(r["name"], local=r["local_md5"], remote=r["box_md5"])
        print("  ✅ %-8s md5 %s verified against the box" % (r["name"], r["box_md5"]))

    n_solo = len(list((LOCAL_ROOT / "logs").glob("*_solo_*.json")))
    print("  solo transcripts pulled: %d (expect %d = 6 x 14)" % (n_solo, 6 * 14))
    if n_solo < 6 * 14:
        raise TransferError("only %d of %d solo transcripts arrived — the ruler "
                            "cannot be recomputed from a partial set"
                            % (n_solo, 6 * 14))

    led = LOCAL_ROOT / "collect_ledger.json"
    led.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("\n  wrote %s — ⛔ NOT yet persisted; terminate will refuse." % led)
    return 0


def cmd_persist(_a):
    led = LOCAL_ROOT / "collect_ledger.json"
    records = json.loads(led.read_text(encoding="utf-8"))
    for r in records:
        d = pathlib.Path(r["local_path"]).parent
        uris = {}
        for fn in ("adapter_model.safetensors", "adapter_config.json"):
            f = d / fn
            if f.exists():
                uris[fn] = push_durable(r["name"], f, HF_REPO,
                                        private=True, subdir=r["name"])
        r["durable_uri"] = uris.get("adapter_model.safetensors")
        r["durable_files"] = uris
        print("  ✅ %-8s persisted -> %s" % (r["name"], r["durable_uri"]))
    led.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("\n  all %d persisted and hub-verified; terminate is now permitted"
          % len(records))
    return 0


def cmd_terminate(a):
    led = LOCAL_ROOT / "collect_ledger.json"
    if not led.exists():
        raise TransferError("no collection ledger — nothing has been verified, "
                            "so nothing may be terminated")
    records = json.loads(led.read_text(encoding="utf-8"))
    print(json.dumps(terminate(a.instance, records), indent=2))
    print("  ✅ terminated after every adapter was verified local AND persisted")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("launch"); p.set_defaults(fn=cmd_launch)
    p.add_argument("--instance-type", default="gpu_1x_a100")
    p.add_argument("--region", default="us-west-1")
    p.add_argument("--ssh-key", default="tlon")
    for name, fn in (("status", cmd_status),):
        q = sub.add_parser(name); q.set_defaults(fn=fn)
    for name, fn in (("provision", cmd_provision), ("train", cmd_train),
                     ("poll", cmd_poll), ("collect", cmd_collect)):
        q = sub.add_parser(name); q.set_defaults(fn=fn)
        q.add_argument("--host", required=True)
        if name == "train":
            # ⛔⛔ REQUIRED, NO DEFAULT — the factorial's corpus axis. A
            # defaulted recipe files a whole batch in an arm nobody chose.
            q.add_argument("--recipe", required=True,
                           choices=("content-free", "content-transient"))
            q.add_argument("--seeds", default=None,
                           help="space-separated seed list. Omit for the "
                                "pipeline's full batch; pass ONE seed for a "
                                "gate run that tests an assumption before the "
                                "batch is bought.")
    q = sub.add_parser("env"); q.set_defaults(fn=cmd_env)
    q.add_argument("--host", required=True)
    q.add_argument("--instance", required=True)
    q = sub.add_parser("persist"); q.set_defaults(fn=cmd_persist)
    q = sub.add_parser("terminate"); q.set_defaults(fn=cmd_terminate)
    q.add_argument("--instance", required=True)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
