# Shot → Reference Prompt Match Report (dm01–dm13, Daniel Mille batch)

**Date:** 2026-06-11
**Goal:** Build `gd_metadata/<proper_name>/<proper_name>_DATA.{json,exr}` for the Daniel
Mille (`dm`) chunk of delivery shots, following `reports/RUNBOOK_gd_metadata.md`.
**Method:** Read-only inspection of `/mnt/projects` (Windows `P:\`) and **`/mnt/ultracache-b`
(Windows `U:\`, the AI input share)**. No writes or deletions were made to either share.
EXR/MOV delivery locations were ignored per the shot notes; only the `Input` videos were used.

This batch supplied **AI input videos** (on `U:\`) rather than render folders. Classification
used the input mp4 name to trace each shot to its originating AnimateDiff render on `/mnt/projects`
(`Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/...`), then a 16-frame diff of that render's
`prompt.json` `prompt_map` against `reference/03_DataPigmentation/`. Inputs with no AnimateDiff
source (rainforest / square edit / biome-lumina sim) were reverse-engineered from the video.

---

## Summary

| Shot | Proper name | Input mp4 (U:\…\AI_INPUT) | AnimateDiff source | Disposition | Ref |
|------|-------------|---------------------------|--------------------|-------------|-----|
| dm01 | `20260324_gd_dm01_v02_14400f` | rainforest_flowers_01.[0001-5658].jpg.mp4 | — (no AD source) | **Reverse-engineered** | — |
| dm02 | `20260325_gd_dm02_v02_14400f` | LANDSCAPE_FOOTHILLS_03_30FPS_2048x3072.mov | LANDSCAPE/FOOTHILLS/V03 | Copied | **F03** (16/16) |
| dm03 | `20260325_gd_dm03_v02_14400f` | OCEAN_V01_SMOOTH_chf3_rhea1.mp4 | FLORA/OCEAN/V01_SMOOTH | Copied | **O03** (16/16) |
| dm04 | `20260326_gd_dm04_v02_14400f` | LANDSCAPE_FOOTHILLS_04_30FPS_2048x3072.mov | LANDSCAPE/FOOTHILLS/V04 | **Generated** (prompt.json, 0/16) | — |
| dm05 | `20260422_gd_dm05_V03_14400f` | FLORA_BAY_04_30FPS_2048x3072.mov | FLORA/BAY/V04 | Copied | **B04** (16/16) |
| dm06 | `20260327_gd_dm06_v01_14400f` | FLORA_OCEAN_04_30FPS_2048x3072.mov | FLORA/OCEAN/V04 | **Generated** (prompt.json, 0/16) | — |
| dm07 | `20260403_gd_dm07_v01_14400f` | FLORA_REDWOOD_03_30FPS_2048x3072.mov | FLORA/REDWOOD/V03 | Copied | **R03** (16/16) |
| dm08 | `20260404_gd_dm08_v01_14400f` | FLORA_FOOTHILLS_02.mp4 | FLORA/FOOTHILLS/V02 | **Generated** (prompt.json, 0/16) | — |
| dm09 | `20260402_gd_dm09_v01_14400f` | edit_001_1920x1920_30fps.mp4 | — (square edit, no AD source) | **Reverse-engineered** | — |
| dm10 | `20260325_gd_dm10_v02_14400f` | BAY_V01_SMOOTH_chf3_rhea1_prores.mov | FLORA/BAY/V01_SMOOTH | **Generated** (prompt.json, 0/16) | — |
| dm11 | `20260420_gd_dm11_v01_14400f` | RF_AI_input.mp4 | — (no AD source) | **Reverse-engineered** | — |
| dm12 | `20260428_gd_dm12_v01_14400f` | FLORA_BAY_v02.mp4 | FLORA/BAY/V02 | Copied | **B01** (15/16*) |
| dm13 | `2026xxxx_gd_dm13_v01_14400f` | input\biome_lumina_dm13\BIOME_LUMINA_DM13_INPUT.mp4 | — (DATALAND biome-lumina sim) | **Reverse-engineered** | — |

\* dm12 frame 0 differs from B01 only by a curated reference edit: source says "red-flowering
**fuchsia**", reference B01 says "red-flowering **California** fuchsia" (identical to the dk04
case). Same video (other 15/16 byte-identical) → copied the reference so the edit is preserved.

Proper names used **verbatim** as supplied (note dm05 carries `_V03_` with a capital V; dm13 is
literally `2026xxxx_…` — date TBD).

### ⚠️ Duplicate entry — needs your confirmation
The user's list had **14 line items**, but two are identical:
- entry #8  `20260404_gd_dm08_v01_14400f` *(FB_TROPICAL_FLOWERS)* — Input `FLORA_FOOTHILLS_02.mp4`
- entry #13 `20260404_gd_dm08_v01_14400f` *(PT_FLORA_FOOTHILLS)* — Input `FLORA_FOOTHILLS_02.mp4`

Same proper name **and** same input → one output folder (`20260404_gd_dm08_v01_14400f`) with
identical metadata. **13 unique folders** were produced. If #13 (PT_FLORA_FOOTHILLS) was meant to
be a separate delivery shot, it needs a distinct proper name (e.g. `…_dm14_…`); say the word and
I'll duplicate the folder under the new name.

Also: dm12's parenthetical is `FS_RAINFOREST_FLOWERS_B`, but its Input is `FLORA_BAY_v02.mp4`,
which is unambiguously FLORA/BAY/V02 → B01. Per your guidance the **Input field is authoritative**,
so it was treated as B01. Flagging the parenthetical/Input mismatch for awareness.

---

## Copied (5)
`reference/03_DataPigmentation/*` `-DATA-*.{json,exr}` copied to
`gd_metadata/<name>/<name>_DATA.{json,exr}`, verified **byte-identical (`cmp` OK, json + exr)**:
F03→dm02, O03→dm03, B04→dm05, R03→dm07, B01→dm12. The source `prompt_map`s use the same 16-key
timebase (`0..1440`) as the reference DATA json, so diffs are exact frame-for-frame.

## Generated from source prompt.json (4)
dm04, dm06, dm08, dm10 each have a full 16-frame AnimateDiff `prompt.json` but **0/16 vs every
reference** — generated directly from the source `prompt_map` via `make_metadata_animatediff.py`
+ `make_embeddings_exr.py` (`DEVICE=cpu`). Source prompt.json copied locally to
`inputs/dm0N_*_prompt.json`. Subjects: dm04 LANDSCAPE/FOOTHILLS/V04, dm06 FLORA/OCEAN/V04,
dm08 FLORA/FOOTHILLS/V02, dm10 FLORA/BAY/V01_SMOOTH.

## Reverse-engineered from video (4)
dm01, dm09, dm11, dm13 have no AnimateDiff source. Prompts reverse-engineered from the input
video with `gen_prompts_gemini.py --match-animatediff` (Vertex `ras-ai-dev`, `gemini-2.5-flash`),
then `make_metadata_animatediff.py` + `make_embeddings_exr.py` (`DEVICE=cpu`). Inputs copied
locally to `inputs/`; prompts in `inputs/generated_prompts/*_prompt.json`.
- **dm01** rainforest_flowers — macro/close-up flowers (roses, lotus, water lilies, succulents).
- **dm09** edit_001 (1920×1920 square) — macro orchids/flowers, blooming.
- **dm11** RF_AI_input — macro flowers (ranunculus, water lilies, white blossoms).
- **dm13** biome_lumina — bioluminescent/translucent fantastical flora & marine organisms
  (same family as dk09/sl09, but a distinct DM13 input video → reverse-engineered fresh).
- **No black/fade intervals** detected in any of the four (content scaled evenly across 16 keys).

**No-missed-copy check:** all 8 generated/reverse-engineered shots diffed against **all 15**
references → **max 0/16** identical frames each. Generating (not copying) was correct.

---

## Verify
All 13 `dm` shots:
- json key set is exactly the 16 keys `[0,96,…,1440]`; every entry has `text/tokens_int/tokens_text`.
- exr is `768×1232`, 2-channel `(G,R)` — identical dims/channels to the reference exrs.
- 5 copies are `cmp`-identical to their reference **json and exr**.

## Read log (read-only shares)
**`/mnt/ultracache-b` (U:\):**
1. Mount check; listed `Contributors/Daniel_Mille/AI_INPUT/` and `…/input/biome_lumina_dm13/`.
2. Copied 4 input videos to local `inputs/` (dm01/dm09/dm11/dm13). Shares unmodified.

**`/mnt/projects` (P:\):**
3. Listed `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/{FLORA,LANDSCAPE}` tree.
4. Read 9 candidate `prompt.json` files; full 16-frame diff vs `reference/03_DataPigmentation`.
5. Copied 4 source `prompt.json` (dm04/06/08/10) to local `inputs/`. Share unmodified.
