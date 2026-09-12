"""⛔⛔ RED-PROOF FOR THE BASE-ASSUMPTION AUDIT.

An audit that reports OK on a base known to be broken is worse than no audit: it
converts an open question into a false reassurance. So the audit is tested
against bases whose faults are already KNOWN AND PAID FOR, and it must find
them:

    Ministral-3-8B   Mistral3ForConditionalGeneration, two layer stacks
                     -> must FAIL the loader check and the stack check
    a lossy template -> must WARN that the train shape drops the system message
    a doubled BOS    -> must not pass silently

⛔⛔ AND `UNKNOWN` MUST NOT BE COUNTED AS A PASS. Qwen's weights are archived off
this machine, so the tensor-level checks cannot run for it. A summary that folds
"could not check" into "checked and fine" is the vacuous pass this whole project
keeps re-finding — one category up from an empty lag cell reading as a failed
one.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "tools"))

pytest.importorskip("transformers")

import act2_base_audit as A                                      # noqa: E402

SYS, USR, ANS = "INSTRUCTION-MARKER", "USER-MARKER", '{"a":1}'
MSGS = [{"role": "system", "content": SYS},
        {"role": "user", "content": USR},
        {"role": "assistant", "content": ANS}]

FAITHFUL = ("{% for m in messages %}<|{{ m['role'] }}|>\n{{ m['content'] }}"
            "<|end|>\n{% endfor %}"
            "{% if add_generation_prompt %}<|assistant|>\n{% endif %}")
LOSSY = ("{% for m in messages %}{% if m['role'] == 'user' %}"
         "{% if loop.last and messages[0]['role'] == 'system' %}"
         "[INST] {{ messages[0]['content'] }}\n\n{{ m['content'] }}[/INST]"
         "{% else %}[INST] {{ m['content'] }}[/INST]{% endif %}"
         "{% elif m['role'] == 'assistant' %} {{ m['content'] }}{{ eos_token }}"
         "{% endif %}{% endfor %}")


def _tok(template, *, bos=None, pad="<pad>"):
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast
    words = ["<pad>", "</s>", "<s>", SYS, USR] + list(ANS)
    tk = Tokenizer(models.WordLevel({w: i for i, w in enumerate(dict.fromkeys(words))},
                                    unk_token="<pad>"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    t = PreTrainedTokenizerFast(tokenizer_object=tk, eos_token="</s>",
                                pad_token=pad, bos_token=bos)
    t.chat_template = template
    return t


# ══ THE AUDIT FINDS WHAT IT IS FOR ══════════════════════════════════════════

def test_a_lossy_template_is_flagged_on_EVERY_shape_the_pipeline_emits():
    a = A.Audit()
    shapes = [("write", MSGS), ("read", MSGS), ("provoke", MSGS)]
    A.audit_template(a, _tok(LOSSY), shapes)
    warns = [r for r in a.rows if r["status"] == A.WARN]
    assert len(warns) == 3, "one per shape — not one for the base"
    assert all("DROPS system" in r["detail"] for r in warns)


def test_a_faithful_template_produces_no_warnings():
    a = A.Audit()
    A.audit_template(a, _tok(FAITHFUL), [("write", MSGS)])
    assert a.counts()[A.WARN] == 0 and a.counts()[A.FAIL] == 0


def test_pad_equals_eos_is_flagged_not_passed():
    a = A.Audit()
    tok = _tok(FAITHFUL, pad="</s>")
    A.audit_tokenizer(a, tok, MSGS, lambda t: "%s %s %s</s>" % (SYS, USR, ANS), 64)
    pads = [r for r in a.rows if r["check"] == "pad token"]
    assert pads and pads[0]["status"] == A.WARN
    assert "position" in pads[0]["detail"]


def test_a_distinct_pad_token_passes():
    a = A.Audit()
    A.audit_tokenizer(a, _tok(FAITHFUL), MSGS,
                      lambda t: "%s %s %s</s>" % (SYS, USR, ANS), 64)
    pads = [r for r in a.rows if r["check"] == "pad token"]
    assert pads and pads[0]["status"] == A.OK


# ══ THE KNOWN-BAD BASE MUST FAIL ════════════════════════════════════════════

MINISTRAL = r"D:\models\mistralai__Ministral-3-8B-Instruct-2512-BF16"


@pytest.mark.skipif(not pathlib.Path(MINISTRAL).is_dir(),
                    reason="Ministral-3 not on this machine")
def test_the_MULTIMODAL_base_FAILS_the_loader_check():
    """⛔⛔ THE MINISTRAL-3 LOSS, ASKED FOR $0 AND WITHOUT WEIGHTS. It cost GPU
    time because the first thing that touched the architecture was the training
    leg. `AutoConfig` answers it at minute zero."""
    a = A.Audit()
    A.audit_load(a, MINISTRAL)
    fails = [r for r in a.rows if r["status"] == A.FAIL]
    assert any("AutoModelForCausalLM" in r["check"] for r in fails), \
        "an unloadable base must FAIL, not warn; got %s" % [r["check"] for r in fails]
    assert any("mistral3" in r["detail"] for r in fails), \
        "and it must name the model_type that is unsupported"


@pytest.mark.skipif(not pathlib.Path(MINISTRAL).is_dir(),
                    reason="Ministral-3 not on this machine")
def test_the_MULTIMODAL_base_FAILS_the_single_stack_check():
    """⛔ Two layer stacks pooled into a contiguous-looking index set — the
    state in which `unfreeze_top=14` trained 36 vision tensors."""
    from transformers import AutoConfig
    a = A.Audit()
    A.audit_scope(a, MINISTRAL, AutoConfig.from_pretrained(MINISTRAL))
    fails = [r for r in a.rows if r["status"] == A.FAIL]
    assert any("ONE transformer-layer stack" in r["check"] for r in fails)
    assert any("vision_tower" in r["detail"] for r in fails)


# ══ UNKNOWN IS NOT A PASS ═══════════════════════════════════════════════════

def test_missing_weights_report_UNKNOWN_not_OK(tmp_path):
    """⛔⛔ THE VACUOUS PASS, ONE CATEGORY UP. The scope claims can only be made
    against real tensor names; with no tensors the only honest answer is that
    the question was not asked."""
    a = A.Audit()
    A.audit_scope(a, tmp_path, None)
    assert a.counts()[A.UNKNOWN] == 1
    assert a.counts()[A.OK] == 0
    assert "NOT a pass" in a.rows[0]["detail"]


def test_UNKNOWN_is_counted_separately_from_OK():
    a = A.Audit()
    a.add("x", "ran", A.OK, "")
    a.add("x", "could not run", A.UNKNOWN, "")
    c = a.counts()
    assert c[A.OK] == 1 and c[A.UNKNOWN] == 1
    assert A.UNKNOWN in c and c[A.UNKNOWN] != 0


def test_the_audit_surfaces_UNKNOWN_in_its_own_summary_text():
    """⭐ A count nobody prints is a count nobody reads."""
    src = (_ROOT / "tools" / "act2_base_audit.py").read_text(encoding="utf-8")
    assert "COULD NOT RUN" in src and "That is not a pass" in src


# ══ WIRED INTO THE PIPELINE ═════════════════════════════════════════════════

def test_the_audit_runs_as_a_pipeline_preflight_BEFORE_training():
    src = (_ROOT / "tools" / "pipeline_fullft.sh").read_text(encoding="utf-8")
    assert "act2_base_audit.py" in src
    assert src.index("step base_audit") < src.index("step train_leg1"), \
        "an audit after the training leg cannot save the training leg"
