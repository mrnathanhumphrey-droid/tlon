"""⛔ A COLD-START EXPERIMENT. Not the bench, not the force probe, not public.

`modal_app.py` says of its `@modal.enter(snap=False)`:

    "Modal's snapshots capture host memory; these weights live in VRAM, which
     a snapshot cannot carry."

⛔⛤ THAT IS STALE. Modal 1.4.3 carries `_experimental_enable_gpu_snapshot` in
the Function proto and `container_io_manager` restores VRAM through a
`CudaCheckpointSession`. Whether it is enabled for THIS account is a server-side
decision, so it is tested rather than assumed — and tested here, on a throwaway
app, rather than on the public bench.

The measurement: `@modal.enter(snap=True)` loads the real speaker. The first run
builds the snapshot and pays the full load; every run after restores it. If the
second cold start is seconds instead of ~18, this is the whole fix and it costs
nothing — no container held open, no `min_containers`.

    modal run puzzle/modal_snapshot_probe.py          # run twice
"""
from __future__ import annotations

import pathlib

import modal

REPO = pathlib.Path(__file__).resolve().parents[1]

#: ⛔ Its own name. Nothing here may touch `tlon-bench`.
app = modal.App("tlon-snapshot-probe")

weights = modal.Volume.from_name("tlon-weights", create_if_missing=True)

CELL = "force-s20624"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch==2.8.0",
                 index_url="https://download.pytorch.org/whl/cu128")
    .pip_install(
        "transformers==5.8.1",
        "peft==0.19.1",
        "bitsandbytes==0.50.1",
        "accelerate==1.13.0",
        "safetensors>=0.4",
        "huggingface_hub>=0.34",
        "fastapi==0.136.1",
        "pydantic>=2.7",
        "PyYAML>=6.0",
    )
    .env({
        "TLON_LEXICON": "lexicon_expanded.yaml",
        "TLON_ADAPTER": "/app/speaker/%s" % CELL,
        "HF_HOME": "/weights/hf",
        "TLON_TEMPERATURE": "0.7",
        "PYTHONUNBUFFERED": "1",
    })
    .add_local_dir(REPO / "tlon", remote_path="/app/tlon")
    .add_local_dir(REPO / "tools", remote_path="/app/tools")
    .add_local_dir(REPO / "puzzle", remote_path="/app/puzzle")
    .add_local_dir(REPO / "runs" / "puzzle_speaker" / CELL,
                   remote_path="/app/speaker/%s" % CELL)
)


@app.cls(
    image=image,
    gpu="A10",
    volumes={"/weights": weights},
    # ⭐ The two flags under test. `enable_memory_snapshot` is the documented
    # host-memory half; the experimental option is what carries VRAM.
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
    timeout=900,
    # ⛔ No secrets, no volumes but the weights cache, no web endpoint. If this
    # app can be reached from outside, it is misconfigured.
)
class SnapProbe:
    @modal.enter(snap=True)
    def load(self):
        """⛔ `snap=True` IS THE EXPERIMENT. The model must be resident BEFORE
        the snapshot is taken or there is nothing in VRAM to carry."""
        import sys
        import time
        sys.path.insert(0, "/app")
        sys.path.insert(0, "/app/tools")
        t0 = time.perf_counter()
        from puzzle.server import speaker
        speaker.load()
        self.load_seconds = time.perf_counter() - t0
        print("SNAPSHOT-PHASE load %.1fs" % self.load_seconds, flush=True)

    @modal.method()
    def ping(self) -> dict:
        """What a first reader would wait for, after the enter phase."""
        import time
        from puzzle.server import speaker
        t0 = time.perf_counter()
        ready = speaker.ready
        return {"ready": ready,
                "enter_load_seconds": round(getattr(self, "load_seconds", -1), 2),
                "ping_seconds": round(time.perf_counter() - t0, 4)}


@app.local_entrypoint()
def main():
    import time
    t0 = time.perf_counter()
    out = SnapProbe().ping.remote()
    wall = time.perf_counter() - t0
    print("\n" + "=" * 58)
    print("COLD START TO FIRST ANSWER: %.1fs wall (client side)" % wall)
    print("  speaker ready       %s" % out["ready"])
    print("  enter-phase load    %.2fs   ⭐ ~0 on a RESTORED snapshot" %
          out["enter_load_seconds"])
    print("  ping                %.4fs" % out["ping_seconds"])
    print("⛔ Run this TWICE. The first run pays the load and writes the")
    print("   snapshot; the second is the number that matters.")
