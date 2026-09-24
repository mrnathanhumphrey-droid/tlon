# The Tlön puzzle — a 7B speaker and a chat window.
#
# ⛔ NOT THE ORACLE'S IMAGE. That one bakes a librarian, chromadb and a search
# stack it needs and this does not. This image carries exactly three things: a
# CUDA runtime, the serving deps, and the parts of the repo the app imports.
#
# ⛔⛔ THE CUDA TAG IS THE ONE DECISION IN HERE THAT CAN SILENTLY COST A DAY.
# It must match the driver on whatever GPU Fly actually schedules. Verify the
# SKU at deploy time and pin to its CUDA line — do not carry this tag forward
# on the assumption it still matches.
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ⛔ torch FIRST and from the CUDA index, alone. Letting a later resolver pick
# it drags in the default CPU/cu12x wheel and every generate() falls back to
# CPU at roughly a minute a turn — slow, not broken, so nothing alerts.
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cu128 \
        torch==2.11.0

COPY puzzle/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

# ── the repo, narrowly ──────────────────────────────────────────────────────
# ⛔ `tools/` is here for ONE reason: `speaker.py` imports the turn shape and the
# backend from `tools/tlon_converse.py` and `tools/act2_backends.py` rather than
# re-spelling either. That import is the guarantee the served prompts are the
# trained prompts. Do not "tidy" it by copying the strings into puzzle/.
COPY tlon/       /app/tlon/
COPY tools/      /app/tools/
COPY puzzle/     /app/puzzle/

# ⭐ The adapter is BAKED. 323 MB, ours, and a machine that boots without it
# serves the untuned base — which answers in English and looks healthy.
# ⛔⛤ v1 IS `dosed-s20624`, NOT `ct-s20624`. The old cell was the pick of
# 2026-09-15 and was never measured on carry; see `speaker.py` for the three
# axes v1 was chosen on. This path and the ENV below must move TOGETHER — a
# COPY of one cell with an ENV naming another boots a machine that cannot find
# its adapter, and `Speaker.load()` fails naming the path, which is the good
# outcome. The bad one is a COPY that still works because the old directory is
# also present: then the container serves last month's weights and nothing says
# so.
COPY runs/puzzle_speaker/dosed-s20624/ /app/speaker/dosed-s20624/

# ⛔⛔⛔ THE LEXICON IS NOT OPTIONAL AND ITS ABSENCE IS SILENT. `classes.py`
# defaults to the FROZEN 156-root lexicon — correctly, so the research
# campaign's verdicts keep their meaning — but this adapter was trained and
# measured on the EXPANDED 218. Without this line the gate refuses any scene
# using one of the 62 expanded-only roots, which is 49.9% of the turns in the
# adapter's own training corpus. It fails CLOSED, so the container comes up
# healthy and merely seems inarticulate. `speaker.py` now refuses to load on a
# hash mismatch; this line is what makes that check pass.
# ⛔ The file ships via `COPY tlon/` above — it is `tlon/grammar/lexicon_expanded.yaml`.
ENV TLON_LEXICON=lexicon_expanded.yaml \
    TLON_ADAPTER=/app/speaker/dosed-s20624 \
    TLON_DB=/data/bench.sqlite3 \
    HF_HOME=/data/hf \
    TLON_TRUST_PROXY=1 \
    TLON_HTTPS=1 \
    TLON_HOST=0.0.0.0 \
    PORT=8080

RUN chmod +x /app/puzzle/docker-entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/app/puzzle/docker-entrypoint.sh"]
