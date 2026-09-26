"""⛔⛔ THE BENCH, ON MODAL — because Fly no longer provisions GPUs.

⛔⛤ THIS REPLACES A FLY DEPLOY THAT BUILT CLEAN AND COULD NOT RUN. `fly.toml`
asked for `gpu_kind = "l40s"` on the strength of a Fly blog post that says GPU
machines are not being retired. The provisioning API disagrees:

    failed to launch VM: GPU machines are no longer supported:
    config.guest.gpu_kind and config.guest.gpus must be unset

A 5.5 GB image was built, pushed and IP-addressed before anything said so.
⭐⭐ A DOCUMENT DESCRIBES INTENT; ONLY THE THING THAT CREATES MACHINES
DESCRIBES REALITY. The GPU below was verified by asking Modal for one and
running `nvidia-smi` on it — A10, 22.1 GiB, torch 2.14+cu130, 7.0s cold — not
by reading that Modal has GPUs.

⭐ THE APP ITSELF IS UNCHANGED. `puzzle.server:app` is imported and served as
an ASGI app; the window, the store, the guard, Turnstile, the speaker and every
prompt come across untouched. Modal supplies a card and a URL, nothing else.

⛔⛔ "SNAPPY, LIKE SOMEONE WAITING ON A PARK BENCH" IS A COLD-START PROBLEM, AND
ONLY ONE OF THE TWO OBVIOUS LEVERS ACTUALLY APPLIES.

  ✅ `scaledown_window` keeps a warm container for minutes after the last
     request. This is the one that matters: nobody mid-conversation ever waits
     for a load, which is where the feeling of a live thing actually lives.

  ⛔ MEMORY SNAPSHOT DOES NOT HELP HERE — but NOT for the reason this said.
     ⛔⛤ It used to read: "Modal's snapshots capture host memory; these weights
     live in VRAM, which a snapshot cannot carry." **That is no longer true.**
     modal 1.4.3 restores VRAM through a `CudaCheckpointSession`, and it was
     tried on 2026-09-26: it works, and it is SLOWER. Cold page load, same app,
     same image, only the flag moved: **22 s -> 52 s**. Restoring a multi-GB
     snapshot out of Modal's storage costs more than reading the weights off
     the volume. The conclusion survived; its reason did not, and a stale
     reason is how the next person gets the wrong answer for a new question.

⛔ `min_containers` is deliberately 0. An A10 held open costs roughly a dollar
an hour, which against the account's credit is days, not months. The first
arrival pays; everyone after them does not. ⭐ If the bench is ever mailed to a
list and should be warm for a known hour, `min_containers=1` for that window is
the lever — a decision with a price, not a default.

⭐ THE FIRST-ARRIVAL COST, MEASURED 2026-09-26 against the live URL: **~22 s
cold, 0.13-0.37 s warm.** About 18 s of that is the load itself.

⛔ AND THE LOAD IS READ-BOUND, NOT QUANTISATION-BOUND — which rules out the
obvious fix. bf16 and NF4 load in the SAME time (17.0 s vs 17.5 s, measured on
`modal_force_probe.py`), so the cost is the ~15 GB of bf16 safetensors coming
off the volume, not the 4-bit conversion. ⭐ The untried lever that follows from
that is a PRE-QUANTISED checkpoint on the volume: ~4.5 GB instead of ~15 GB, a
one-off save, no experimental platform features.
"""
from __future__ import annotations

import pathlib

import modal

REPO = pathlib.Path(__file__).resolve().parents[1]

app = modal.App("tlon-bench")

#: ⛔ The 14 GB base model lives on a VOLUME, not in the image. Baking it would
#: make every code change re-push 14 GB, and Modal caches the volume between
#: cold starts so the second boot does not re-download it.
weights = modal.Volume.from_name("tlon-weights", create_if_missing=True)
#: ⭐ The bench itself — one SQLite file, so a reader's conversation survives a
#: scale-to-zero. It is the reason `max_containers` is 1 below.
bench = modal.Volume.from_name("tlon-bench-db", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.12")
    # ⛔ torch FIRST and alone, from the CUDA index — the same reasoning the
    # Dockerfile gives: letting a later resolver pick it drags in a wheel built
    # against the wrong runtime and every generate() fails at import depth.
    .pip_install("torch==2.8.0", index_url="https://download.pytorch.org/whl/cu128")
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
    # ⛔⛔ `.env()` COMES BEFORE EVERY `add_local_*`, AND MODAL ENFORCES IT:
    #   "An image tried to run a build step after using `image.add_local_*`"
    # Local files are attached at container START, not baked, so that a code
    # change does not rebuild the image — which means no build step may
    # follow them. `.env()` is a build step. Ordering here is not style.
    .env({
        # ⛔⛔ THE LANGUAGE THIS ADAPTER SPEAKS. Without it the library default
        # is the FROZEN 156-root lexicon and the gate refuses 49.9% of the
        # turns in the speaker's own training corpus — failing CLOSED, so the
        # container comes up healthy and merely seems inarticulate.
        # `speaker.py` refuses to load on a hash mismatch; this is what makes
        # that check pass.
        "TLON_LEXICON": "lexicon_expanded.yaml",
        "TLON_ADAPTER": "/app/speaker/force-s20624",
        # ⛔⛔ THE DIAL IS ON, AND WITHOUT IT THIS CELL SERVES THE SAME
        # MONOCULTURE v1 DID. Measured: the speaker chooses `ka` 100% of
        # the time whatever it is answering (12 nodes x 5 forces, n=24 a
        # cell) because its corpus never varied the PROMPT's force, and a
        # target that is varied but unpredictable trains to its mode. The
        # corpus cannot fix that; the draw is imposed here.
        # ⛔ `TLON_KI_WEIGHT` IS DELIBERATELY ABSENT. Setting it AT ALL —
        # even to its own default — selects the legacy even-split table,
        # which serves `ka` 7.4% and `ki` 38.3%.
        "TLON_FORCE_TABLE": "1",
        "TLON_TURNSTILE_SITEKEY": "0x4AAAAAAFCzgoZ1d8Y7fEc4",
        "TLON_DB": "/bench/bench.sqlite3",
        # ⛔⛔ ON THE VOLUME, OR THERE IS NO LOG. `scaledown_window` is 300
        # seconds: five quiet minutes and a container-local file is gone,
        # along with every error and every turn it ever held. `server.py`
        # would derive this path from `TLON_DB` anyway; it is spelled out
        # because the ops manual has to be able to name the file.
        "TLON_LOG_DB": "/bench/log.sqlite3",
        "HF_HOME": "/weights/hf",
        # ⭐ Modal terminates TLS and sets the forwarded headers, so the bench
        # cookie may be Secure and the per-IP limit may trust the proxy.
        "TLON_HTTPS": "1",
        "TLON_TRUST_PROXY": "1",
        # ⛔ OFF. `server._startup` warms on a thread for Fly's benefit; here
        # the warm is owned by `@modal.enter()` below, which runs BEFORE the
        # container is given any traffic. Two warms would load twice.
        "TLON_PRELOAD": "0",
        "PYTHONUNBUFFERED": "1",
    })
    # ⛔ THE SAME THREE TREES THE DOCKERFILE COPIES, AND FOR THE SAME REASON:
    # `puzzle/speaker.py` imports the turn shape and the backend from `tools/`
    # rather than re-spelling either, and that import is the guarantee that the
    # served prompts are the trained prompts.
    .add_local_dir(REPO / "tlon", remote_path="/app/tlon")
    .add_local_dir(REPO / "tools", remote_path="/app/tools")
    .add_local_dir(REPO / "puzzle", remote_path="/app/puzzle")
    # ⭐ The adapter IS baked: 323 MB, ours, and a container that comes up
    # without it serves the untuned base, which scored 0.0% on write and would
    # answer every visitor in English while looking entirely healthy.
    .add_local_dir(REPO / "runs" / "puzzle_speaker" / "force-s20624",
                   remote_path="/app/speaker/force-s20624")
)


@app.cls(
    image=image,
    gpu="A10",
    volumes={"/weights": weights, "/bench": bench},
    # ⛔⛔ THE TURNSTILE SECRET. Without it `turnstile.preflight()` refuses to
    # start — which is the intended behaviour, because a public GPU endpoint
    # with an unverified challenge in front of it reports perfectly healthy.
    #
    # ⛔⛔ AND `tlon-proxy`, WHICH IS A SEPARATE SECRET ON PURPOSE. It holds
    # `TLON_PROXY_SECRET`, the value `guard.client_ip()` requires before it
    # will believe an `X-Tlon-Client-IP` header. Without it the last
    # `X-Forwarded-For` entry is CLOUDFLARE'S EGRESS ADDRESS, so every reader
    # on earth shares one identity and the 12-turns-per-IP limit silently
    # becomes a second global limit — it fails OPEN and nothing looks wrong.
    #
    # ⭐ IT IS ITS OWN SECRET RATHER THAN A SECOND KEY IN `tlon-turnstile`
    # because `modal secret create --force` REPLACES the whole secret. Adding
    # a key to the existing one means re-supplying the Turnstile key in the
    # same breath, and a mistyped or omitted one there takes the challenge
    # down with it. Two secrets, two blast radii.
    # ⛔⛔ AND `tlon-admin`, WHICH MUST EXIST BEFORE THIS WILL DEPLOY. It holds
    # `TLON_ADMIN_TOKEN`, the bearer the ban and snapshot endpoints check. Its
    # absence is a deploy failure ON PURPOSE: the alternative is an app that
    # comes up healthy with its admin door permanently 404, which is only
    # discovered on the day somebody needs to ban a reader.
    #
    #     python -c "import secrets; print(secrets.token_urlsafe(32))"
    #     modal secret create tlon-admin TLON_ADMIN_TOKEN=<that value>
    #
    # ⭐ ITS OWN SECRET, for the reason the two above already give: `modal
    # secret create --force` REPLACES a whole secret, so adding a key to an
    # existing one means re-supplying the other keys in the same breath, and a
    # mistyped Turnstile key there takes the challenge down with it.
    secrets=[modal.Secret.from_name("tlon-turnstile"),
             modal.Secret.from_name("tlon-proxy"),
             modal.Secret.from_name("tlon-admin")],
    # ⭐ Warm for five minutes after the last request. This is the number that
    # makes the bench feel alive: nobody mid-conversation waits for a load.
    scaledown_window=300,
    # ⛔⛤ GPU MEMORY SNAPSHOT WAS TRIED HERE ON 2026-09-26 AND MADE THIS APP
    # SLOWER. Kept as a note so it is not tried a third time without new
    # information.
    #
    #     enable_memory_snapshot=True,
    #     experimental_options={"enable_gpu_snapshot": True},
    #
    # It DOES work — modal 1.4.3 restores VRAM through a `CudaCheckpointSession`,
    # the logs show "Restoring Function from memory snapshot", and `load()` ran
    # twice across three cold starts. It is simply slower for this workload:
    # restoring a multi-GB snapshot out of Modal's storage costs more than
    # reading the weights off the `tlon-weights` volume.
    #
    #     cold page load, same app, same image:   22 s  ->  52 s
    #
    # ⛔⛔ AND THE NUMBER THAT SOLD IT WAS A CONFOUND. A throwaway probe read
    # "62.7 s -> 10.8 s", but its slow arm included a FIRST-EVER IMAGE PULL and
    # its fast arm did not. Two things differed and the image caching was doing
    # the work. The honest comparison is the one above: one app, one image,
    # only the flag moved.
    # ⛔⛔ ONE. The bench is a SQLite file on a volume; two containers would not
    # share it, so a reader's conversation would vanish whenever they were
    # routed elsewhere — data loss that presents as a UI bug. It is also what
    # `guard.MAX_CONCURRENT` already assumes: one process, one generation.
    max_containers=1,
    timeout=300,
)
class Bench:
    @modal.enter(snap=False)
    def load(self):
        """⛔ BEFORE ANY TRAFFIC. `@modal.enter` runs while the container is
        still being made ready, so the first reader meets a loaded model rather
        than a queue.

        ⛔ `snap=False`. Memory snapshots CAN carry VRAM now, contrary to what
        this docstring said for months — but measured on this app they cost 30
        extra seconds of cold start rather than saving any. See `@app.cls`.
        """
        import sys

        sys.path.insert(0, "/app")
        sys.path.insert(0, "/app/tools")
        from puzzle.server import speaker

        speaker.load()
        print("tlön · speaker loaded in %.1fs" % (speaker.load_seconds or 0),
              flush=True)

    @modal.enter(snap=False)
    def after_restore(self):
        """⛔⛔ EVERYTHING A SNAPSHOT FROZE THAT MUST NOT BE SHARED.

        `snap=False` enters run AFTER a restore, on every container. This one
        exists for a single line, and that line is not optional:

        `speaker._force_rng = random.Random()` is seeded from OS entropy AT
        IMPORT, and the import happens inside the snapshot phase above. So a
        snapshot freezes the generator's state, and **every restored container
        would draw the identical sequence of reply forces** — the dial would
        look varied and repeat itself exactly on each cold start. Subtle,
        invisible in any health check, and a direct regression of the thing the
        dial was shipped to fix.

        ⭐ The other two candidates were checked and are safe: `TS.preflight()`
        and every secret read happen in the ASGI `startup` hook inside `web()`,
        which is after restore, and `logbook` opens its SQLite connection per
        call rather than holding one at import — so no stale handle to a
        reader's conversation is carried across.
        """
        import sys

        sys.path.insert(0, "/app")
        from puzzle import speaker as SP

        SP._force_rng.seed()
        print("tlön · post-restore: force rng reseeded", flush=True)

    @modal.asgi_app()
    def web(self):
        import sys

        sys.path.insert(0, "/app")
        sys.path.insert(0, "/app/tools")
        from puzzle.server import app as fastapi_app

        return fastapi_app
