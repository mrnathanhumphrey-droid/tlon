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


def cmd_train(a):
    ssh(a.host, KEY,
        "cd ~/tlon && nohup bash tools/pipeline_retrain.sh "
        "> ~/retrain_stdout.log 2>&1 &")
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
    q = sub.add_parser("persist"); q.set_defaults(fn=cmd_persist)
    q = sub.add_parser("terminate"); q.set_defaults(fn=cmd_terminate)
    q.add_argument("--instance", required=True)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
