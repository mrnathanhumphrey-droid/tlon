# s20625

- `adapter_model.safetensors` — pulled from box 6b23bdf34e1445b0a871813798190038 and verified md5 `ee0c52ade6ee16acaba9d8454135d001`, computed ON THE BOX before the pull.
- `adapter_config.json` — ⛔ **RECONSTRUCTED**, not pulled. The box was terminated by its own watchdog before the config was collected. It is copied from a sibling adapter trained by the same recipe and VERIFIED against these weights: the safetensors declares 392 tensors over exactly the 7 modules the config targets, at LoRA rank 32. The only field that ever differs between sibling configs is `target_modules` ORDER, which peft treats as a set; it is sorted here.
- F-LOCAL and solo transcripts: see ../SALVAGE_2026_09_04.md
