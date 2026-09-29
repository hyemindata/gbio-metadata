# Shot → Reference Prompt Match Report (dk01–dk09)

**Date:** 2026-06-11
**Goal:** Build `gd_metadata/<proper_name>/<proper_name>_DATA.{json,exr}` for the `dk`
chunk of delivery shots, following `reports/RUNBOOK_gd_metadata.md`.
**Method:** Read-only inspection of `/mnt/projects` (Windows `P:\` mounted at
`/mnt/projects`). No writes or deletions were made to the project share. EXR (`R:\…`
NUKE_OUT) paths were not needed and were ignored per the shot notes.

For this chunk the user supplied the originating **AnimateDiff INPUT folder** for 8 of 9
shots, so classification was a direct 16-frame diff of each source `prompt_map` against
`reference/03_DataPigmentation/`. dk09 is a DATALAND simulation with no prompt.

---

## Summary

| Shot | Proper name | Source | Disposition | Reference |
|------|-------------|--------|-------------|-----------|
| **dk01** | `20260421_gd_dk01_v01_14400f` | AnimateDiff LANDSCAPE/OCEAN/V01 | **Generated** (has prompt.json, no reference) | — none |
| **dk02** | `20260414_gd_dk02_v01_14400` | AnimateDiff FLORA/FOOTHILLS/V03 | Copied | **F01** (16/16) |
| **dk03** | `20260414_gd_dk03_v01_14400` | AnimateDiff FLORA/FOOTHILLS/V04 | Copied | **F02** (16/16) |
| **dk04** | `20260414_gd_dk04_v01_14400` | AnimateDiff FLORA/BAY/V02 | Copied | **B01** (15/16*) |
| **dk05** | `20260414_gd_dk05_v01_14400` | AnimateDiff FLORA/REDWOOD/V02 | Copied | **R01** (16/16) |
| **dk06** | `20260421_gd_dk06_v01_14400f` | AnimateDiff LANDSCAPE/FOOTHILLS/V03 | Copied | **F03** (16/16) |
| **dk07** | `20260414_gd_dk07_v01_14400` | AnimateDiff LANDSCAPE/BAY/V02 | Copied | **B02** (16/16) |
| **dk08** | `20260421_gd_dk08_v01_14400f` | AnimateDiff LANDSCAPE/OCEAN/V04 | Copied | **O01** (16/16) |
| **dk09** | `20260414_gd_dk09_v01_14400` | DATALAND BIOME LUMINA sim (video) | **Generated** (reverse-engineered) | — none |

\* dk04 frame 0 differs only by a manual reference edit: source says "red-flowering
**fuchsia**", reference B01 says "red-flowering **California** fuchsia". Same video
(15/16 other frames byte-identical); copied the reference so the curated edit is kept.

Proper names used **verbatim** as supplied (note dk01/dk06/dk08 carry the trailing `f`;
dk02–05/07/09 do not).

---

## Copied (7)

Each `reference/03_DataPigmentation/*` `-DATA-*.{json,exr}` copied to
`gd_metadata/<name>/<name>_DATA.{json,exr}` and verified **byte-identical (`cmp` OK)**:
F01→dk02, F02→dk03, B01→dk04, R01→dk05, F03→dk06, B02→dk07, O01→dk08.

The source `prompt_map`s use the same 16-key timebase (`0..1440`) as the reference DATA
json, so the diffs are exact frame-for-frame. These are confirmed same-video matches, so
the reference json (with any prior curated edits) is the correct delivery content.

## Generated (2)

- **dk01** — LANDSCAPE/OCEAN/V01 *has* a full 16-frame `prompt.json` (a distinct
  underwater coral-reef walk: turquoise water, coral, yellow tangs/neon wrasse) but
  **no reference matches it**. Generated directly from its source `prompt_map` via
  `make_metadata_animatediff.py` + `make_embeddings_exr.py` (`DEVICE=cpu`). Source copied
  locally to `inputs/dk01_LANDSCAPE_OCEAN_01_prompt.json`.
- **dk09** — DATALAND **BIOME LUMINA** simulation (`AIS_Biome_Lumina_Input.mp4`,
  1290×1190, 30 fps, 106.6 s). No prompt ever existed → reverse-engineered 16 prompts
  from the video with `gen_prompts_gemini.py --match-animatediff` (Vertex `ras-ai-dev`,
  `gemini-2.5-flash`); subject is bioluminescent/translucent fantastical flowers & marine
  organisms. No black/fade intervals detected (content scaled evenly across all 16 keys).
  Video copied locally to `inputs/dk09_biome_lumina.mp4`; prompts in
  `inputs/generated_prompts/dk09_biome_lumina_prompt.json`.

**No-existing-reference check (user request):** both generated shots were diffed against
**all 15** reference scenes — **max 0/16 identical frames** for each, and neither
subject (distinct ocean walk; bioluminescent flowers) corresponds to a reference scene.
Generating (not copying) was correct for both.

---

## Verify

All 9 `dk` shots:
- json key set is exactly the 16 keys `[0,96,…,1440]`; every entry has
  `text/tokens_int/tokens_text`.
- exr is `768×1232`, 2-channel `(G,R)` — identical dims/channels to the reference exrs
  (the runbook's "1232×768" is the 77·16 × 768 layout; OpenEXR reports it as W=768,
  H=1232, same as every reference and copied file).
- 7 copies are `cmp`-identical to their reference json **and** exr.

## DATALAND path note

dk09's source resolves **without** the `Biophilia - Google Gradient Canopy` prefix:
`/mnt/projects/Team/Delaney/DATALAND/AI_SANCTUARY/IMG_SEQ/AIS_Biome_Lumina_Input.mp4`
(the shot notes' `P:\Team\Delaney\…` is correct as-is). The `R:\…AI_Sanctuary_NUKE_OUT`
EXR locations were not mounted and not needed.

## Read log (`/mnt/projects`, read-only)

1. Mount check + listed the 8 AnimateDiff INPUT folders; confirmed each has `prompt.json`.
2. Read all 8 source `prompt_map`s; full 16-frame diff vs `reference/03_DataPigmentation`.
3. dk09: searched for the DATALAND path; listed `Team/Delaney/DATALAND/AI_SANCTUARY/IMG_SEQ/`
   (single file `AIS_Biome_Lumina_Input.mp4`); copied it to `inputs/` (share unmodified).
