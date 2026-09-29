# Runbook: building `gd_metadata/` for a chunk of delivery shots

End-to-end process for turning delivery shots (slNN) into `gd_metadata/<proper_name>/
<proper_name>_DATA.{json,exr}`. Worked examples: `sl01-sl09_prompt_match_report.md`
(mixed copy/GAN/sim) and `dk01-dk09_prompt_match_report.md` (INPUT-folder-supplied batch:
7 copies, 1 generated-from-prompt.json, 1 reverse-engineered).

## Hard rules
- **`/mnt/projects` is READ-ONLY.** Never write to or delete from it. Notify on every read.
  (`P:\` on Windows == `/mnt/projects` here; project share is
  `/mnt/projects/Biophilia - Google Gradient Canopy/`.)
- Use the user's **proper names verbatim** (e.g. `20260421_gd_slNN_v01_<N>f`).

## Environments
- `animatediff` (`/home/hyemin/anaconda3/envs/animatediff`): torch/diffusers/SD1.5/OpenEXR
  — runs `make_metadata_animatediff.py` + `make_embeddings_exr.py`.
- `gsutil` (`/raid/hyemin/Projects/conda_data/conda_envs/gsutil`): google-genai + vertexai
  — runs `gen_prompts_gemini.py`. ADC is configured; gcloud project **`ras-ai-dev`**.

## Metadata format (must match)
- `*_DATA.json`: dict keyed by **16 frame indices on an 8 fps timebase** `0,96,…,1440`
  (every 12 s), each value `{text, tokens_int, tokens_text}`.
- `*_DATA.exr`: 2-channel `(R,G)`, size `(77 * Nprompts) x 768` → **1232×768** for 16 prompts.
- All final artworks are 4 min; the `_<N>f` suffix is the delivered video's frame count
  (varies by fps — but use whatever the user specifies).

## Step 1 — Classify each shot
For each shot, find the source `prompt.json` in its asset folder on the share, then
compare its prompt text to `reference/03_DataPigmentation/**/*-DATA-*.json`:
- **Match** (subject/first-line aligns; full 16-frame diff usually identical) → copy the
  reference `_DATA.json/.exr`.
- **Has prompt.json, no reference** → generate metadata from that prompt_map (Step 3).
- **Video only** (GAN/sim/no prompt ever existed) → reverse-engineer from video (Step 2).
Topaz/upscale folders have no prompt.json — trace back to the originating AnimateDiff
render (e.g. `FLORA_BAY_04` → `FLUID_SIM_BASE_ANIMATEDIFF/FLORA/BAY/V04`).

**Classification mechanics (learned on the `dk` batch):**
- The user may hand you the **AnimateDiff INPUT folder directly** (the `dk` batch did this
  for 8/9 shots). When so, skip the share hunt — go straight to that folder's `prompt.json`.
- The source `prompt.json` is the AnimateDiff render config; its **`prompt_map` uses the
  same 16-key set `0..1440`** as the reference DATA json, so classify by diffing the
  `prompt_map` text against each reference DATA `text`, **frame-for-frame**. Script-free
  one-liner: load `json[...]["prompt_map"]` and compare to `ref[k]["text"]` per key.
- A **15/16 near-match is still the same video** — the lone differing frame is a curated
  manual edit in the *reference* (e.g. dk04: source "red-flowering fuchsia" vs reference
  "red-flowering **California** fuchsia"). Treat it as a Match and **copy the reference**
  so the curated edit is preserved. Do NOT downgrade to "no match" just for <16/16.
- **Has prompt.json but 0/16 vs every reference → generate from that same prompt.json**
  (it already has `prompt_map`); no video reverse-engineering needed (dk01 = a distinct
  LANDSCAPE/OCEAN walk with no matching reference). Before generating, confirm 0/16 vs
  *all* references so you don't miss a copy candidate.

## Step 2 — Reverse-engineer prompts from video (video-only shots)
Put the delivered video in `inputs/slNN_<tag>.mp4`, then (gsutil env):
```
DEVICE unused here.  python gen_prompts_gemini.py inputs/slNN_<tag>.mp4 \
    --match-animatediff -o inputs/generated_prompts/slNN_<tag>_prompt.json
```
`--match-animatediff` emits the 16 AnimateDiff keys, auto-detects black fades via
`blackdetect`, drops them, and scales the non-black content [0, black_start−0.3 s] evenly
across the keys. Prompts always begin `"A cinematic "`; shot type fits the frame (not
forced to landscape). Black frames are reported. Review the printed prompts before Step 3.

## Step 3 — Produce `_DATA.json` + `_DATA.exr`
Copy step (matches):
```
cp <ref>-DATA-*.json gd_metadata/<name>/<name>_DATA.json
cp <ref>-DATA-*.exr  gd_metadata/<name>/<name>_DATA.exr
cmp <ref>.json gd_metadata/<name>/<name>_DATA.json   # verify byte-identical
```
Generate step (video-only / prompt.json shots), run in `animatediff` env on CPU because
the big GPUs are usually full (4 GB GPU3 can't hold SD1.5 float32):
```
DEVICE=cpu python make_metadata_animatediff.py <prompt_json> -o gd_metadata/<name>/<name>_DATA.json
DEVICE=cpu python make_embeddings_exr.py       <prompt_json> -o gd_metadata/<name>/<name>_DATA.exr
```
(`make_*` scripts honor the `DEVICE` env var; default `cuda`. Both accept the
`{"prompt_map":{...}}` shape `gen_prompts_gemini.py` writes — **and the raw AnimateDiff
`prompt.json` works as-is**, since it already contains a `prompt_map` key. So for a
"has prompt.json, no reference" shot you can feed the source `prompt.json` straight in.)
On CPU the scripts print a benign `float16 cannot run with cpu` warning then succeed —
verify the output (keys, non-NaN exr) rather than trusting/fearing the warning.

## Step 4 — Verify
All shots should share the same 16-key set `[0..1440]` and exr `1232×768 (R,G)`; each json
entry has `text/tokens_int/tokens_text`; copied files `cmp`-identical to their reference
(check **both** json and exr). Cross-check generated shots: diff their text vs *all*
references and confirm 0/16 (so a copy wasn't missed).

**EXR dimension gotcha:** OpenEXR reports the dataWindow as **W=768, H=1232** with
channels `('G','R')` — this is the *same* as every reference/copied exr, so it's correct.
The "1232×768 (R,G)" in this runbook is the logical `(77·16)×768` layout, not OpenEXR's
W×H. Verify by matching a reference exr's reported dims, not by expecting literal 1232×768.

## Source-path quirks (learned on the `dk` batch)
- **DATALAND sources can lack the `Biophilia - Google Gradient Canopy` prefix.** dk09's
  `P:\Team\Delaney\DATALAND\AI_SANCTUARY\IMG_SEQ` resolved at
  `/mnt/projects/Team/Delaney/DATALAND/AI_SANCTUARY/IMG_SEQ/` (no project-name prefix).
  If a `P:\` path 404s under the share, retry without the prefix.
- That `IMG_SEQ` folder held a **ready-made mp4** (`AIS_Biome_Lumina_Input.mp4`), so no
  JPG→mp4 build was needed — copy it locally to `inputs/` and feed Step 2 directly.
- The `R:\…AI_Sanctuary_NUKE_OUT\…` EXR locations are not mounted and (per shot notes)
  can be ignored unless a specific reason arises.
- **Proper-name suffixes vary within a batch** — some shots are `…_14400f`, some `…_14400`
  (no trailing `f`). Use the user's name verbatim per shot; don't normalize.

## Input-video batches (learned on the `dm` / Daniel Mille batch)
This batch handed over **AI input videos on the `U:\` share** instead of render folders.
Worked example: `reports/dm01-dm13_prompt_match_report.md` (5 copy, 4 generate, 4 reverse-eng).
- **`U:\` == `/mnt/ultracache-b`** — a second STRICTLY READ-ONLY share (same rules as
  `/mnt/projects`: never write/delete, notify on every read). Inputs lived under
  `U:\Contributors\<artist>\AI_INPUT\` (and `…\input\<shot>\`). Copy each input video to
  local `inputs/` and process there.
- **Classify via the Input mp4 name, not the parenthetical.** The user's rule: the `Input`
  field is authoritative (EXR/MOV ignored). Map the input name to its AnimateDiff render on
  `/mnt/projects/Biophilia…/Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/<BIOME>/<SCENE>/<VER>`,
  read that render's `prompt.json`, and diff `prompt_map` vs `reference/` frame-for-frame.
  Naming maps cleanly: `FLORA_BAY_04`→FLORA/BAY/V04, `FLORA_REDWOOD_03`→FLORA/REDWOOD/V03,
  `LANDSCAPE_FOOTHILLS_03`→LANDSCAPE/FOOTHILLS/V03, `OCEAN_V01_SMOOTH`/`BAY_V01_SMOOTH`→
  FLORA/{OCEAN,BAY}/V01_SMOOTH, etc. The `_30FPS_2048x3072` / `_chf3_rhea1` suffixes are
  Topaz-upscale tags on the same render — ignore them for classification.
- **The render→reference index is NOT 1:1** — confirm by diffing, never assume. E.g.
  LANDSCAPE/FOOTHILLS/V03→F03 here, but FLORA/FOOTHILLS/V03→F01 on the `dk` batch. Several
  renders (LANDSCAPE/FOOTHILLS/V04, FLORA/OCEAN/V04, FLORA/FOOTHILLS/V02, FLORA/BAY/V01_SMOOTH)
  had a full `prompt.json` but **0/16 vs all 15 references → generate from the prompt.json**.
- **`B01`'s "California fuchsia" curated edit recurs.** FLORA/BAY/V02→B01 came up 15/16 with
  the same lone frame-0 diff as `dk04` (source "red-flowering fuchsia" vs ref "…California
  fuchsia"). Same video → copy the reference to keep the edit. (15/16 ⇒ copy, per Step 1.)
- **No-AnimateDiff inputs → reverse-engineer (Step 2)** straight from the input video:
  rainforest-flowers / square `edit_001` comp / `BIOME_LUMINA` DATALAND sims have no render
  folder. `gen_prompts_gemini.py` only sends 16 extracted JPG frames to Gemini (not the whole
  video), so large inputs (>1 GB) are fine; none had black fades this batch.
- **Watch for duplicate / mismatched line items.** Two entries (#8 FB_TROPICAL_FLOWERS,
  #13 PT_FLORA_FOOTHILLS) shared one proper name AND one input → one folder (user confirmed
  keep-one). One shot's parenthetical disagreed with its Input (`FS_RAINFOREST…` vs
  `FLORA_BAY_v02.mp4`); Input wins. Flag these rather than guessing; a "14-item" list can
  legitimately yield fewer unique folders.
- **Placeholder names are used verbatim** — dm13 was literally `2026xxxx_gd_dm13_v01_14400f`
  (date TBD); build the folder as given and remind the user to supply the date.
