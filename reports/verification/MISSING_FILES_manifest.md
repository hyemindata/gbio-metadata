# Verification PDFs — status & missing-file manifest

**Generated:** `reports/verification/<proper_name>_VERIFY.pdf` (one per shot)
**Generator:** `make_verification_pdfs.py` (rerun any time; results cached per video)

Each PDF lines up the **three resources in time**:

- **SOURCE** = INPUT mp4 (the simulation imagery fed in — what the prompt describes)
- **ARTWORK** = OUTPUT mp4 (the final abstract data-pigmentation piece)
- **PROMPT** = `gd_metadata/<name>/<name>_DATA.json` (16 prompts, 8 fps keys `0…1440`)

Time alignment is **normalised**: prompt *i* (0–15) → fraction *i*/15 across each video's
non-black content (leading/trailing black fades auto-trimmed), so the three line up even
though source/artwork fps and length differ. Each row prints the prompt's 8 fps key plus
the actual source/artwork frame number and timestamp used.

> Note observed in the copied shots: the OUTPUT artwork **starts as an empty white frame
> and fills in**, so the artwork at fraction 0 (prompt #00) is often blank. That is a real
> property of the piece, not a metadata error.

---

## dk update (2026-06-12): real AnimateDiff sources wired in

All 9 `dk` PDFs were regenerated using the authoritative source videos from
`P:\…\FLUID_SIM_BASE_ANIMATEDIFF\…` (the `00_<seed>_<slug>.mp4` render in each folder,
native **8 fps**, copied to `inputs/sources/dk0N_*.mp4`). dk09's source is the DATALAND
`AIS_Biome_Lumina_Input.mp4`. dk01 & dk09 still lack the artwork (their delivery EXRs are
on `R:\…AI_Sanctuary_NUKE_OUT`, which is not mounted) so their artwork column stays a
placeholder. dk02–dk08 are full (real source + reference OUTPUT artwork).

## dm update (2026-06-12): real sources + delivery MOVs wired in

All 13 `dm` PDFs were regenerated from the read-only `U:\` share — **no copy, no symlink**,
just direct ffmpeg frame extraction (paths hardcoded in `EXTRA_PATHS` in the generator):
- **source** = the `AI_INPUT` video (Topaz upscales `*_30FPS_2048x3072.mov` @16 GB, or the
  smaller mp4s; the 4 reverse-eng sources stayed local in `inputs/`).
- **artwork** = the delivery MOV in `AI_Sanctuary_EXR\update_010526\<name>.mov` (~63–68 GB
  ProRes, 4224×5616 @ 60 fps). dm01–dm12 are now **full**; **dm13 has no MOV yet** (in
  progress) so it stays source-only.

## Done — 25 / 31 (full source + artwork + prompt)

18 originally-copied shots, **plus dk02–dk08** (real P:\ source + reference OUTPUT),
**plus dm01, dm04, dm06, dm08, dm09, dm10, dm11** (real U:\ source + delivery MOV).
(dm02, dm03, dm05, dm07, dm12 were already full and now use the real U:\ source + MOV too.)

Both INPUT and OUTPUT mp4s came with the matched `reference/03_DataPigmentation` scene
(prompt text 16/16 identical to that scene's DATA json):

| Shot | Ref scene | Shot | Ref scene | Shot | Ref scene |
|------|-----------|------|-----------|------|-----------|
| sl01 | F05 | dk02 | F01 | dm02 | F03 |
| sl03 | O03 | dk03 | F02 | dm03 | O03 |
| sl04 | R03 | dk04 | B01 | dm05 | B04 |
| sl06 | B04 | dk05 | R01 | dm07 | R03 |
| sl07 | F04 | dk06 | F03 | dm12 | B01 |
| sl08 | B03 | dk07 | B02 |      |     |
|      |     | dk08 | O01 |      |     |

---

## Partial — 6 / 31 (built with placeholders; artwork still missing)

Source-only PDFs (artwork column is a placeholder):

| Shot | Why no artwork |
|------|----------------|
| sl02 | OUTPUT artwork not provided |
| sl05 | OUTPUT artwork not provided |
| sl09 | OUTPUT artwork not provided |
| dk01 | delivery EXR on `R:\…NUKE_OUT\LANDSCAPE_OCEAN_01` (not mounted) |
| dk09 | delivery EXR on `R:\…NUKE_OUT\BIOME_LUMINA_V1` (not mounted) |
| dm13 | delivery MOV not produced yet (shot in progress) |

*(was 13; dk02–dk08 and dm01/04/06/08/09/10/11 are now full — see dk/dm updates above)*

To fill in a missing artwork later, drop the video in `inputs/artworks/` with the shot id
in the filename (e.g. `sl02_artwork.mp4`) — or add it to `EXTRA_PATHS` in the generator —
then rerun with `--force`. Outstanding: the 3 `sl` OUTPUT artworks, the 2 `dk` R:\ EXRs
(mount `R:\` to use), and dm13's MOV once the shot is finished.

---

## Rerun

```
python make_verification_pdfs.py            # builds only shots whose PDF doesn't exist yet
python make_verification_pdfs.py --force    # rebuild everything
python make_verification_pdfs.py sl02 dk01 --force   # rebuild only named shots
```

A plain rerun never regenerates an existing PDF, so after dropping new videos use `--force`
(optionally scoped to the shot ids you added).
