# Shot → Reference Prompt Match Report (sl01–sl09)

**Date:** 2026-06-10
**Goal:** For each shot, locate the source `prompt.json` in the asset folder on the
project share, then match its prompt text against the existing text metadata in
`reference/03_DataPigmentation/` to decide which shots were already generated (so
prior edits can be kept for the same video) and which still need work.

**Method:** Read-only inspection of `/mnt/projects` (Windows `P:\` mounted at
`/mnt/projects`). No writes or deletions were made to the project share.

---

## Summary: matches vs. no-match

| Shot | Source `prompt.json`? | Reference match | Confidence |
|------|----------------------|-----------------|-----------|
| **sl01** | ✅ found | **Foothills/05** — `CHP3-DP-SCE-F05-SEUNGMIN-DATA-250801` | exact, 16/16 frames |
| **sl02** | 🛠️ none (solution in progress) | — (GAN output, not AnimateDiff) | prompt to be reverse-engineered from video |
| **sl03** | ✅ found | **Ocean/03** — `CHP3-DP-SCE-O03-SEUNGMIN-DATA-250724` | exact, 16/16 frames |
| **sl04** | ✅ found | **Redwoods/03** — `CHP3-DP-SCE-R03-SEUNGMIN-DATA-250724` | exact, 16/16 frames |
| **sl05** | 🛠️ none (solution in progress) | — (StyleGAN2 source) | prompt to be reverse-engineered from video |
| **sl06** | ✅ found (via FLORA/BAY/**V04**) | **Bay/04** — `CHP3-DP-SCE-B04-SEUNGMIN-DATA-250924` | exact, 16/16 frames |
| **sl07** | ✅ found | **Foothills/04** — `CHP3-DP-SCE-F04-SEUNGMIN-DATA-250801` | exact, 16/16 frames |
| **sl08** | ✅ found | **Bay/03** — `CHP3-DP-SCE-B03-SEUNGMIN-DATA-250729` | exact, 16/16 frames |
| **sl09** | 🛠️ none (solution in progress) | — (DATALAND simulation, neither GAN nor AnimateDiff) | prompt to be reverse-engineered from video |

---

## Matches (6) — which is which

All six AnimateDiff shots map cleanly, and crucially **all 16 frame-prompts are
byte-identical to the existing reference DATA json** — i.e. confirmed same video.
(sl06 reaches its AnimateDiff source via inference — see the sl06 deep-dive below.)

| Shot | Reference scene | Subject |
|------|-----------------|---------|
| **sl01** | **F05** | Foothills landscape — golden hills + green succulents, orange/yellow wildflowers, midday sky |
| **sl03** | **O03** | Bright pink coralline algae, golden kelp blades, turquoise water |
| **sl04** | **R03** | White Wake Robin flowers aging to pink, redwood forest floor |
| **sl06** | **B04** | Tidy Tips, canary-yellow rays tipped white, over the bay |
| **sl07** | **F04** | Wild hyacinth, blue flowers against green grass + golden hills |
| **sl08** | **B03** | Ithuriel's Spear, lavender-blue umbel over the bay |

Since these are exact, same-video matches, **the existing `reference/` json for each
already reflects the correct content** — prior edits in the text are preserved there;
nothing to regenerate for the text metadata.

### Shot source paths (matches)

- **sl01** — `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/LANDSCAPE/FOOTHILLS/V01/2024-11-22T17-33-11-sample-epicphotogasm_yphotoreal/` (seed `739768325166`)
- **sl03** — `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/FLORA/OCEAN/V01_SMOOTH/2025-03-04T17-18-25-sample-epicphotogasm_yphotoreal/` (seed `636209611587`)
- **sl04** — `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/FLORA/REDWOOD/V03/2025-04-12T10-41-37-sample-epicphotogasm_yphotoreal/` (seed `160794840`)
- **sl06** — `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/FLORA/BAY/V04/2025-04-18T19-25-13-sample-epicphotogasm_yphotoreal/` (seed `1813802596`) — *delivered as the Topaz upscale `Render/HyeMin/TOPAZ/FLORA/BAY/FLORA_BAY_04/…`*
- **sl07** — `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/FLORA/FOOTHILLS/V01_SMOOTH/2025-03-11T17-51-00-sample-epicphotogasm_yphotoreal/` (seed `189633773276`)
- **sl08** — `Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/FLORA/BAY/V03/2025-04-15T20-41-45-sample-epicphotogasm_yphotoreal/` (seed `1557470335`)

(all under `/mnt/projects/Biophilia - Google Gradient Canopy/`)

---

## No match (3)

- **sl02** — see the dedicated **sl02 deep-dive** section below. Resolved: it is a
  **GAN output** (not AnimateDiff), so there is no source `prompt.json` and the
  metadata prompts must be **reverse-engineered from the video**.
- **sl05** — see the dedicated **sl05 deep-dive** section below. It is a **StyleGAN2
  output** (no text-to-video prompt), so there is no source `prompt.json` and the
  metadata prompts must be **reverse-engineered from the video**.

(**sl06** was initially a no-match — the Topaz folder has no `prompt.json` — but it was
resolved to an AnimateDiff match via inference; see the **sl06 deep-dive** below.)

- **sl09** — see the dedicated **sl09 deep-dive** section below. It is a **DATALAND
  simulation source** — **neither GAN nor AnimateDiff** — so there is no source
  `prompt.json` and the metadata prompts must be **reverse-engineered from the video**.

---

## Open questions / next steps

- **sl02** — RESOLVED (GAN output). Next step: reverse-engineer the prompt set from the
  video `inputs/sl02_OCEAN_01.mp4`, then generate metadata. See deep-dive below.
- **sl05** — RESOLVED (GAN output). Next step: reverse-engineer the prompt set from the
  video `inputs/sl05_REDWOODS_03_GAN.mp4`, then generate metadata. See deep-dive below.
- **sl06** — RESOLVED (AnimateDiff match → B04). The Topaz folder had no `prompt.json`,
  but it was traced to FLORA/BAY/**V04** by inference and confirmed 16/16. See deep-dive.
- **sl09** — RESOLVED as a reverse-engineer case (DATALAND simulation, neither GAN nor
  AnimateDiff). Next step: reverse-engineer the prompt set from the video
  `inputs/sl09_blumina_02.mp4`, then generate metadata. See deep-dive below.

---

## sl02 deep-dive (RESOLVED)

**Conclusion:** Despite the AnimateDiff-style filename (`00_<seed>_<slug>…`), sl02's
source is actually a **GAN output, cropped to the target resolution** — *not* an
AnimateDiff text-to-video render. There is therefore **no source `prompt.json`**, and
the metadata prompts for sl02 must be **reverse-engineered from the video itself**.

**Source asset (read-only, on the share):**
`/mnt/projects/Biophilia - Google Gradient Canopy/Team/Seungmin/Houdini/source/OCEAN_01/`

| Property | Value |
|---|---|
| Seed (in filename) | `382330814616` |
| Slug (in filename) | `A-cinematic-close-up-of-bright-pink-coralline-alga` (truncated) |
| Frames | **14,400** (`00000`–`14399`, `%05d`) |
| Resolution | **683 × 1024** (portrait, RGB) |
| Sidecars | none — only `Thumbs.db` (no `prompt.json`, no metadata) |

**Evidence / how this was determined:**
- Seed `382330814616` appears **nowhere else on the entire project share** (searched
  the whole `Biophilia…` tree); the only coralline-algae renders in the AnimateDiff
  tree use sl03's seed `636209611587`. So the filename's AnimateDiff-style naming is
  misleading — there is no originating AnimateDiff render folder to recover.
- The filename slug matches O03's first prompt only because the slug was carried over
  in naming; it does **not** imply an AnimateDiff prompt set exists.
- Confirmed by the user: the simulation source is a GAN output cropped to resolution.

**Working video (saved in this repo):** `inputs/sl02_OCEAN_01.mp4` — a visually-lossless
MP4 built from the OCEAN_01 JPG sequence. This is the basis for reverse-engineering the
sl02 prompts (the share asset was only read, never modified).

**Next step for sl02 metadata:** reverse-engineer the prompt(s) from
`inputs/sl02_OCEAN_01.mp4`, then run the metadata generator. The subject is bright-pink
coralline algae (akin to O03), but the prompt set should be derived from the video, not
copied from O03, since this is a different (GAN) source.

---

## sl05 deep-dive (RESOLVED)

**Conclusion:** sl05's source is a **StyleGAN2 output** — a GAN, not a text-to-video
render — so there is **no source `prompt.json`** and no associated text prompt at all.
The metadata prompts for sl05 must be **reverse-engineered from the video itself**.

**Source asset (read-only, on the share):**
`/mnt/projects/Biophilia - Google Gradient Canopy/Team/Seungmin/Houdini/source/REDWOODS_03_GAN/`

| Property | Value |
|---|---|
| Generator | StyleGAN2 (`network-snapshot-082880`, model `stylegan2-ca_all_biomes-cleaned-2048`, gpus4 batch16 gamma10) |
| Seed / prompt | none — GAN latent walk, no text conditioning |
| Frames | **14,400** (`00000`–`14399`, `%05d`) |
| Resolution | **1024 × 1536** (portrait, RGB) |
| Sidecars | none — only `Thumbs.db` (no `prompt.json`, no metadata) |

**Evidence / how this was determined:**
- The filename itself encodes the StyleGAN2 model and snapshot
  (`03_redwoods_stylegan2-ca_all_biomes-cleaned-2048…network-snapshot-082880`), i.e. a
  GAN frame export, not an AnimateDiff/text-to-video render.
- No seed, slug, or prompt text in the naming, and no sidecar metadata in the folder.

**Working video (saved in this repo):** `inputs/sl05_REDWOODS_03_GAN.mp4` — a
visually-lossless MP4 built from the REDWOODS_03_GAN JPG sequence. This is the basis for
reverse-engineering the sl05 prompts (the share asset was only read, never modified).

**Next step for sl05 metadata:** reverse-engineer the prompt(s) from
`inputs/sl05_REDWOODS_03_GAN.mp4`, then run the metadata generator. The subject is a
redwoods scene (cf. the Redwoods reference scenes), but the prompt set must be derived
from the video, since this GAN source had no text prompt to begin with.

---

## sl06 deep-dive (RESOLVED via inference)

**Conclusion:** sl06 *is* an AnimateDiff shot. The delivered asset is a Topaz upscale
whose folder has no `prompt.json`, but the originating render was traced from the
`FLORA_BAY_04` naming to **AnimateDiff `FLORA/BAY/V04`**, which **matches reference
Bay/04 (B04, Tidy Tips) — 16/16 frames identical**.

**Delivered asset (read-only, on the share):**
`Render/HyeMin/TOPAZ/FLORA/BAY/FLORA_BAY_04/2_PNG_30FPS_2048x3072/FLORA_BAY_04_chf3_rhea1/%06d.png`
(Topaz upscale, 2048×3072, 30fps; no `prompt.json` in this tree).

**Originating AnimateDiff render (source of the prompt):**
`Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF/FLORA/BAY/V04/2025-04-18T19-25-13-sample-epicphotogasm_yphotoreal/`
(seed `1813802596`).

**How the inference was made (multiple corroborating signals):**
- **Naming:** `FLORA_BAY_04` → FLORA biome, BAY, index 04 → AnimateDiff `FLORA/BAY/V04`
  (the BAY tree has exactly `V01_ORIGINAL`, `V01_SMOOTH`, `V02`, `V03`, `V04`).
- **Subject:** V04's prompt is **Tidy Tips**, and its render mp4 slug is
  `…Tidy-Tips_their-daisy-like…` — the same subject as reference B04.
- **Exact diff:** V04 `prompt.json` vs B04 `…-DATA-…json` → **16/16 frames identical**.
- **Cross-check vs sl08:** BAY/V03 is Ithuriel's Spear (= sl08/B03), so V04≠V03; the
  index lines up cleanly (V03→B03, V04→B04).

**Working video (saved in this repo):** `inputs/sl06_FLORA_BAY_04.mp4` (built from the
Topaz PNG sequence).

**Result:** Treated like the other exact matches — the existing **B04** reference json
already reflects the correct content; **no prompt reverse-engineering needed** for sl06.

---

## sl09 deep-dive (reverse-engineer in progress)

**Conclusion:** sl09's source is a **DATALAND simulation** (`biome_lumina_sim`,
`blumina_02`) — it is **neither a GAN output nor an AnimateDiff render**, so no source
`prompt.json` exists and no text prompt was ever associated with it. The metadata
prompts for sl09 must be **reverse-engineered from the video itself**.

**Source path (from the shot notes):**
`P:\Team\Seungmin\DATALAND\biome_lumina_sim\source\05\blumina_02_%05d.jpg`
(Used range `00000`–`01799`). Note this path lacks the `Biophilia - Google Gradient
Canopy` prefix the other shots have, so it did not resolve under the project share
during the read-only sweep.

**Working video (saved in this repo):** `inputs/sl09_blumina_02.mp4` — the basis for
reverse-engineering the sl09 prompts. (The file was initially placed as
`sl07_blumina_02.mp4`; renamed to `sl09_…` since `blumina_02` is the sl09 DATALAND
source — sl07 is the already-confirmed Foothills/04 match.)

**Next step for sl09 metadata:** reverse-engineer the prompt(s) from
`inputs/sl09_blumina_02.mp4`, then run the metadata generator. The prompt set must be
derived from the video, since this simulation source had no text prompt to begin with.

---

## Reference scene catalog (first-frame prompts)

For traceability, the 16 reference scenes in `reference/03_DataPigmentation/`:

| Scene | File | First-frame subject |
|-------|------|---------------------|
| Bay/01 | `CHP3-DP-SCE-B01-LANEY-DATA-250723` | red-flowering California fuchsia over rocky outcrop |
| Bay/02 | `CHP3-DP-SCE-B02-LANEY-DATA-250729` | Bodega Bay at sunrise |
| Bay/03 | `CHP3-DP-SCE-B03-SEUNGMIN-DATA-250729` | Ithuriel's Spear (← **sl08**) |
| Bay/04 | `CHP3-DP-SCE-B04-SEUNGMIN-DATA-250924` | Tidy Tips, yellow/white rays (← **sl06**) |
| Foothills/01 | `CHP3-DP-SCE-F01-LANEY-DATA-250723` | Farewell to Spring, pink/crimson petals |
| Foothills/02 | `CHP3-DP-SCE-F02-LANEY-DATA-250723` | Sky Lupine over golden foothills |
| Foothills/03 | `CHP3-DP-SCE-F03-LANEY-DATA-250723` | foothills clear morning, yellow fiddlenecks |
| Foothills/04 | `CHP3-DP-SCE-F04-SEUNGMIN-DATA-250801` | wild hyacinth (← **sl07**) |
| Foothills/05 | `CHP3-DP-SCE-F05-SEUNGMIN-DATA-250801` | foothills + succulents, orange/yellow (← **sl01**) |
| Ocean/01 | `CHP3-DP-SCE-O01-LANEY-DATA-250729` | shallow sunlit underwater, silver light |
| Ocean/02 | `CHP3-DP-SCE-O02-LANEY-DATA-250729` | rocky reef, cup corals, Garibaldi |
| Ocean/03 | `CHP3-DP-SCE-O03-SEUNGMIN-DATA-250724` | bright pink coralline algae (← **sl03**) |
| Redwoods/01 | `CHP3-DP-SCE-R01-LANEY-DATA-250729` | golden grasses at redwood base |
| Redwoods/02 | `CHP3-DP-SCE-R02-SEUNGMIN-DATA-250724` | redwood sorrel carpet, white flowers |
| Redwoods/03 | `CHP3-DP-SCE-R03-SEUNGMIN-DATA-250724` | white Wake Robin flowers (← **sl04**) |

---

## gd_metadata build (done 2026-06-11)

Built `gd_metadata/<proper_name>/<proper_name>_DATA.{json,exr}` for all 9 shots (flat,
one folder per shot). Names supplied by user (all `20260421_gd_slNN_v01_14400f`).

- **Copied (6)** from `reference/03_DataPigmentation`, byte-identical (`cmp` OK), 16
  frames, exr 1232×768 (R,G): sl01←F05, sl03←O03, sl04←R03, sl06←B04, sl07←F04, sl08←B03.
- **Generated (3)** from video via `gen_prompts_gemini.py --match-animatediff` (Vertex
  `ras-ai-dev`, `gemini-2.5-flash`) → `inputs/generated_prompts/*_prompt.json` →
  `make_metadata_animatediff.py` + `make_embeddings_exr.py` (run `DEVICE=cpu`): sl02,
  sl05, sl09. **16 prompts each, keys 0…1440 — identical to the AnimateDiff shots** —
  exr 1232×768 (R,G). All 9 now share one key set.
- **Black frames dropped:** trailing fade-outs detected via ffmpeg `blackdetect`
  (sl02 ~0.2 s, sl09 ~9.2 s, sl05 none). The non-black content [0, black_start−0.3 s] is
  scaled evenly across the 16 keys, so no key lands on a black frame.
- Note: sl02's GAN content is an all-biomes landscape walk (not coralline algae).
- Code change: `make_metadata_animatediff.py` / `make_embeddings_exr.py` now honor a
  `DEVICE` env var (default `cuda`) so they can run on CPU.

## Read log (`/mnt/projects`, read-only)

1. Mount check + `find prompt.json` in the 5 AnimateDiff folders.
2. Read first prompt of the 5 `prompt.json` files.
3. `find *.json` in the 4 non-AnimateDiff source folders (sl02 / sl05 / sl06 / sl09).
4. Re-read the 5 `prompt.json` files for the full 16-frame diff against `reference/`.
5. sl02: share-wide hunt for seed `382330814616`; listed `OCEAN_01/` (14,400 JPGs,
   683×1024, only `Thumbs.db` sidecar); read first frame dimensions. Read-only — the
   `inputs/sl02_OCEAN_01.mp4` in this repo was generated from the sequence without
   modifying the share.
6. sl05: listed `REDWOODS_03_GAN/` (14,400 JPGs, 1024×1536, only `Thumbs.db` sidecar);
   read first frame dimensions; confirmed StyleGAN2 naming. Read-only — the
   `inputs/sl05_REDWOODS_03_GAN.mp4` in this repo was generated from the sequence
   without modifying the share.
7. sl06: listed AnimateDiff `FLORA/BAY/` versions; read all 5 `prompt.json` first
   prompts; full 16-frame diff of `FLORA/BAY/V04/prompt.json` vs B04 reference; read
   V04 render seed/slug. Read-only — `inputs/sl06_FLORA_BAY_04.mp4` was built from the
   Topaz PNG sequence without modifying the share.
8. sl09: no share read (path unresolved under the share). Classified from shot notes as
   a DATALAND simulation source; video provided as `inputs/sl09_blumina_02.mp4` for
   prompt reverse-engineering.
