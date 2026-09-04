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

# ⛔⛔ A PROVISIONING TOOL MUST NOT DIE ON A `print`. Windows defaults stdout to
# cp1252, which cannot encode the glyphs this project's output is written in, so
# `provision` crashed on the "box pinned" line — AFTER the clone and the SHA
# check had already run. On this path that is dangerous rather than cosmetic:
# `collect` and `persist` perform irreversible work (an upload, a ledger write),
# and a crash between the action and the record is exactly the shape that lost
# s20620 — the thing happened and nothing wrote it down.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from act2_provision import (TransferError, launch, instances,  # noqa: E402
                            md5_local, push_durable, ssh, terminate,
                            verify_checksum, verify_pulled_set)

REPO_GIT = "https://github.com/mrnathanhumphrey-droid/tlon.git"
HF_REPO = "keyzersoze04/tlon-act2-adapters"
KEY = pathlib.Path.home() / ".ssh" / "tlon"
#: ⛔ Solo transcripts per build — the asym_recert procedure the frozen ruler is
#: computed over. Named once; the completeness check derives from it and from
#: the manifest's own length, never from a hardcoded batch size.
SOLO_PER_BUILD = 14


def _roots(root: str):
    """-> (remote, local) for a run root.

    ⛔⛔ THESE WERE MODULE CONSTANTS PINNED TO `retrain12`, AND THAT IS A BUG THE
    MOMENT A SECOND RUN EXISTS. The gate box writes to `retrain12_ct`; `collect`
    would have read a manifest from a directory that does not exist on it, and
    the failure would arrive at the one stage whose whole job is not to lose an
    adapter.
    """
    if not root or "/" in root or "\\" in root or root.startswith("."):
        raise TransferError("bad run root %r" % (root,))
    return "~/tlon/runs/act2/%s" % root, pathlib.Path("runs/act2") / root
# ⛔ `NEW = ("s20624", ...)` lived here, unused, a hardcoded batch list one
# careless reference away from becoming the thing that decides what a run
# contains. Same class as the `== 6` that killed the gate box. Deleted rather
# than left to be found.


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
    # ⛔ The instance NAME is how a human tells two live boxes apart. Pinned to
    # "tlon-retrain12", both arms of the factorial would wear one label in the
    # console — and the first thing anyone does in a bad moment is read that
    # console. Defaults to the run root it will write to.
    r = launch(instance_type=a.instance_type, region=a.region,
               ssh_key_name=a.ssh_key, name="tlon-%s" % a.root)
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
    from act2_provision import _lambda_key
    key = _lambda_key()
    if not key:
        raise TransferError(
            "no Lambda API key locally — set LAMBDA_API_KEY or put it in the "
            "env file under CLOUD_LAMBDA=. The box's watchdog cannot terminate "
            "without it, and refuses to arm, so the pipeline would halt.")
    # ⛔⛔ THE HF TOKEN IS NOW LOAD-BEARING, SO ITS ABSENCE IS A REFUSAL. This
    # used to fall back to `hf = ""` and ship an empty export. Persistence is a
    # pipeline stage now: an empty token means the run trains for hours and then
    # cannot save anything, discovered at the one moment when the artifacts
    # exist only on a box that is already terminating itself.
    hf = os.environ.get("HF_TOKEN", "")
    envf = pathlib.Path(r"D:\physics_detector\.env")
    if not hf and envf.exists():
        m = re.search(r"^HF_TOKEN=(.+)$",
                      envf.read_text(encoding="utf-8", errors="replace"), re.M)
        hf = m.group(1).strip().strip('"').strip("'") if m else ""
    if not hf:
        raise TransferError(
            "no HF_TOKEN — refusing to provision. The box persists its own "
            "artifacts as a pipeline stage, so a run without a write token is a "
            "run that cannot save what it makes.")
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

    # ⛔⛔ AND PROVE THE SAVE PATH, NOT ONLY THE KILL PATH. The two are symmetric
    # obligations: a box that cannot terminate costs money, and a box that
    # cannot persist costs the work. Only the second one is unrecoverable, and
    # it is the one that had no arm-time probe until now. ⭐ It WRITES — a
    # read-only token passes a read probe and fails at the end of the run.
    save = ssh(a.host, KEY,
               ". ~/.tlon_env && cd ~/tlon && ~/venv/bin/python "
               "tools/act2_box_persist.py --root /tmp/_probe --repo %s probe"
               % HF_REPO, check=False)
    print("  persist path from the box: %s" % save.strip().splitlines()[-1:])
    if "verified writable" not in save:
        raise TransferError(
            "the box CANNOT WRITE to hf://%s (%s). Persistence is a pipeline "
            "stage; without it the run would train for hours and then have "
            "nowhere to put the result." % (HF_REPO, save.strip()[-300:]))
    print("  ✅ the box can persist its own artifacts")
    return 0


#: Pipelines this orchestrator may start. ⛔ A CLOSED SET, not a free string —
#: `--pipeline` is interpolated into a remote shell command.
PIPELINES = ("pipeline_retrain.sh", "pipeline_solo_regen.sh",
             "pipeline_positive_control.sh")
#: ⛔ The recipe is the FACTORIAL'S CORPUS AXIS, so it belongs to the pipeline
#: that builds corpora and to no other. Requiring it everywhere would file a
#: transcript re-run into an arm it is not in.
NEEDS_RECIPE = ("pipeline_retrain.sh",)


def cmd_train(a):
    if a.pipeline not in PIPELINES:
        raise TransferError("unknown --pipeline %r" % (a.pipeline,))
    env = "ROOT=runs/act2/%s" % a.root
    if a.pipeline in NEEDS_RECIPE:
        # ⛔⛔ THE RECIPE IS PASSED EXPLICITLY AND THE PIPELINE REQUIRES IT.
        # There is no default on either side: a batch filed into an arm nobody
        # chose is an adapter in no cell of the factorial, and the matrix is
        # rebuilt from exactly these labels once the scrollback is gone.
        if a.recipe not in ("content-free", "content-transient",
                            "content-persistent"):
            raise TransferError("unknown --recipe %r" % (a.recipe,))
        env += " RECIPE=%s" % a.recipe
    elif a.recipe:
        raise TransferError(
            "--recipe applies only to %s — %s does not build a corpus, and a "
            "recipe label on a run that has no corpus axis is a caveat pointing "
            "at nothing" % (", ".join(NEEDS_RECIPE), a.pipeline))
    if a.seeds:
        # ⭐ A GATE RUN trains ONE adapter to test an assumption before the
        # batch is bought. The pipeline's full seed literal is untouched.
        env += " SEEDS='%s'" % a.seeds
        print("  ⭐ SINGLE-SEED GATE RUN: seeds=%s" % a.seeds)
    if a.builds:
        env += " BUILDS='%s'" % a.builds
    if a.suppression_window is not None:
        # ⭐ The release-suppression dose (prereg 765b6787). It reaches the cell
        # name, the corpus manifest and factorial.json, so an adapter can always
        # say which treatment it received.
        env += " SUPPRESSION_WINDOW=%d" % a.suppression_window
        print("  ⭐ DOSE: suppression_window=%d" % a.suppression_window)
    if a.model_lag:
        # ⭐ THE GATE READ RUNS ON THE BOX, WHILE THE GPU IS STILL RENTED.
        # Leaving it to a later ssh means keeping a box alive for it or buying a
        # second one — and an unexecuted runbook step is how s20620 was lost.
        env += " MODEL_LAG=1"
        print("  ⭐ MODEL-LAG GATE READ ARMED — prereg abde6124 §4, "
              "12 chains x 10 turns, cardless, unconstrained")
    # ⛔ Sources the credential file so the watchdog it spawns inherits the
    # key it needs. A non-interactive ssh does NOT read ~/.bashrc.
    # ⛔ The stdout log is named after the pipeline: `retrain_stdout.log` was
    # correct for exactly one pipeline, and two runs sharing a laptop and a name
    # is how a diagnosis gets read off the wrong box.
    stem = a.pipeline.replace("pipeline_", "").replace(".sh", "")
    ssh(a.host, KEY,
        "cd ~/tlon && . ~/.tlon_env && %s nohup bash tools/%s "
        "> ~/%s_stdout.log 2>&1 &" % (env, a.pipeline, stem))
    print("  %s · %s" % (a.pipeline, env))
    print("  ✅ pipeline launched under nohup; the on-instance watchdog arms "
          "itself before any GPU time is spent")
    print("  poll with: %s poll --host %s --root %s"
          % (sys.argv[0], a.host, a.root))
    return 0


def cmd_poll(a):
    remote, _local = _roots(a.root)
    # ⛔ `pipeline_retrain.log` was hardcoded — the same class as the batch size
    # and the `adapter_s*` glob: correct for exactly one run, and silently empty
    # for the next. An empty tail reads as "nothing has happened yet", which is
    # the most reassuring possible way to be wrong about a box on a meter.
    print(ssh(a.host, KEY,
              "tail -5 %s/pipeline_*.log 2>/dev/null; "
              "echo ---; ls ~/DONE ~/FAILED 2>/dev/null" % remote,
              check=False))
    return 0


def cmd_collect(a):
    """⛔⛔ THE STAGE WHOSE ABSENCE LOST s20620."""
    remote, local_root = _roots(a.root)
    print("collecting from %s -> %s" % (remote, local_root.as_posix()))
    local_root.mkdir(parents=True, exist_ok=True)
    raw = ssh(a.host, KEY, "cat %s/manifest.json" % remote)
    manifest = json.loads(raw)
    print("box manifest lists %d adapters" % len(manifest))

    for name in manifest:
        dest = local_root / ("adapter_%s" % name)
        dest.mkdir(parents=True, exist_ok=True)
        _run(["scp", "-i", str(KEY), "-q",
              "ubuntu@%s:%s/adapter_%s/adapter_model.safetensors" % (a.host, remote, name),
              "ubuntu@%s:%s/adapter_%s/adapter_config.json" % (a.host, remote, name),
              str(dest)])
    _run(["scp", "-i", str(KEY), "-q", "-r",
          "ubuntu@%s:%s/logs" % (a.host, remote), str(local_root)])
    # ⛔ GLOB, NOT ONE NAME. `pipeline_retrain.log` was hardcoded here too —
    # the third instance of the class in this file, after the `6 * 14` solo
    # count and `poll`'s tail. For any other pipeline this pulled nothing and
    # said nothing, and the run log is the artifact re-running cannot
    # regenerate. ⭐ Found by the guard written for `poll`, which is the point
    # of writing guards against the class instead of the instance.
    _run(["scp", "-i", str(KEY), "-q",
          "ubuntu@%s:%s/pipeline_*.log" % (a.host, remote),
          str(local_root)])

    records = plan_collection(manifest, local_root)
    # ⛔ SET first, then per-artifact checksum. An empty pull passes every
    # per-file check trivially, because there are no files to check.
    verify_pulled_set(expected=list(manifest),
                      found=[r["name"] for r in records if r["local_md5"]])
    for r in records:
        verify_checksum(r["name"], local=r["local_md5"], remote=r["box_md5"])
        print("  ✅ %-8s md5 %s verified against the box" % (r["name"], r["box_md5"]))

    # ⛔⛔ DERIVED FROM THE MANIFEST, NOT A HARDCODED BATCH SIZE. This read
    # `6 * 14`, which is correct for exactly one run and silently wrong for
    # every other — a single-adapter gate run would have been refused as a
    # partial pull of a batch it was never part of.
    want_solo = len(manifest) * SOLO_PER_BUILD
    n_solo = len(list((local_root / "logs").glob("*_solo_*.json")))
    print("  solo transcripts pulled: %d (expect %d = %d x %d)"
          % (n_solo, want_solo, len(manifest), SOLO_PER_BUILD))
    if n_solo < want_solo:
        raise TransferError("only %d of %d solo transcripts arrived — the ruler "
                            "cannot be recomputed from a partial set"
                            % (n_solo, want_solo))

    led = local_root / "collect_ledger.json"
    led.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("\n  wrote %s — ⛔ NOT yet persisted; terminate will refuse." % led)
    return 0


def cmd_persist(a):
    _remote, local_root = _roots(a.root)
    led = local_root / "collect_ledger.json"
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
    _remote, local_root = _roots(a.root)
    led = local_root / "collect_ledger.json"
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
    # ⛔⛔ DEFAULTS THAT NEVER MATCHED REALITY. These read `gpu_1x_a100` /
    # `us-west-1`; every run this project has actually done was on
    # `gpu_1x_a100_sxm4` in `us-west-2` (runs/act2/retrain12/INSTANCE.json), and
    # on 2026-09-04 the PCIe A100 had no capacity in ANY region — so the default
    # was not merely wrong, it was unlaunchable, and it failed with a bare
    # HTTP 400 that says nothing about capacity.
    # ⭐ It matters beyond convenience: the 40 GiB VRAM wall the pipeline asserts
    # against, and the 15,598 s/adapter timing reference, are both properties of
    # THIS card. A default that silently moves the hardware moves the ruler.
    p.add_argument("--instance-type", default="gpu_1x_a100_sxm4")
    p.add_argument("--region", default="us-west-2")
    p.add_argument("--ssh-key", default="tlon")
    p.add_argument("--root", default="retrain12",
                   help="run tree this box will write to; also its name in the "
                        "Lambda console, so two live boxes are tellable apart")
    for name, fn in (("status", cmd_status),):
        q = sub.add_parser(name); q.set_defaults(fn=fn)
    # ⛔⛔ EVERY STAGE THAT TOUCHES A RUN TREE TAKES --root. It was a module
    # constant pinned to `retrain12`, which is correct for exactly one run and
    # silently wrong for the next — and the stage it would have broken is
    # `collect`, whose entire job is not to lose an adapter.
    for name, fn in (("provision", cmd_provision), ("train", cmd_train),
                     ("poll", cmd_poll), ("collect", cmd_collect)):
        q = sub.add_parser(name); q.set_defaults(fn=fn)
        q.add_argument("--host", required=True)
        if name in ("poll", "collect", "train"):
            q.add_argument("--root", required=(name == "train"),
                           default="retrain12",
                           help="run tree under runs/act2/ — e.g. retrain12 "
                                "(the control batch), retrain12_ct, solo_regen")
        if name == "train":
            # ⛔ REQUIRED, NO DEFAULT. Which procedure a box runs is not a thing
            # to infer: the last box to be handed a defaulted answer trained the
            # right thing and then died at a stage that could not describe it.
            q.add_argument("--pipeline", required=True, choices=PIPELINES)
            # ⛔⛔ THE FACTORIAL'S CORPUS AXIS. No default: a defaulted recipe
            # files a whole batch in an arm nobody chose. Required in practice
            # by `cmd_train` for the pipelines that build corpora, and REFUSED
            # for the ones that do not.
            q.add_argument("--recipe", default=None,
                           choices=("content-free", "content-transient",
                                    "content-persistent"))
            q.add_argument("--suppression-window", type=int, default=None,
                           help="release-suppression dose. -1 bars nothing and "
                                "is valid ONLY with --recipe "
                                "content-persistent (a dose arm, never a "
                                "factorial cell).")
            q.add_argument("--seeds", default=None,
                           help="space-separated seed list. Omit for the "
                                "pipeline's full batch; pass ONE seed for a "
                                "gate run that tests an assumption before the "
                                "batch is bought.")
            q.add_argument("--builds", default=None,
                           help="space-separated build list for a probe re-run "
                                "(pipeline_solo_regen.sh). Omit for its full "
                                "set.")
            q.add_argument("--model-lag", action="store_true",
                           help="run the model-side lag profile on the box "
                                "after each adapter is persisted — the gate "
                                "read, prereg abde6124. Needs a GPU, so it "
                                "cannot be deferred to the laptop.")
    q = sub.add_parser("env"); q.set_defaults(fn=cmd_env)
    q.add_argument("--host", required=True)
    q.add_argument("--instance", required=True)
    q = sub.add_parser("persist"); q.set_defaults(fn=cmd_persist)
    q.add_argument("--root", default="retrain12")
    q = sub.add_parser("terminate"); q.set_defaults(fn=cmd_terminate)
    q.add_argument("--instance", required=True)
    q.add_argument("--root", default="retrain12")
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
