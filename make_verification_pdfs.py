#!/usr/bin/env python3
"""
Build one verification PDF per delivery shot, lining up the three resources in time:

    SOURCE video (INPUT / simulation fed in)  |  ARTWORK video (OUTPUT / final piece)  |  PROMPT

The 16 prompts live on an 8 fps timebase (keys 0,96,...,1440). Source and artwork
videos have varying fps / length, so prompts are aligned by NORMALISED position:
prompt i (i = 0..15) -> fraction i/15 across each video's non-black content span.
Trailing/leading black fades are detected and excluded so no key lands on black.

Per shot the PDF has a header page (all file paths, video specs, flags) followed by
16 rows, each: source frame | artwork frame | prompt text + frame#/timestamps.

Usage:
    python make_verification_pdfs.py                # all shots that have both videos
    python make_verification_pdfs.py sl01 dm05      # only the named shots
"""
import json, glob, os, re, subprocess, sys, hashlib

from fpdf import FPDF

ROOT = os.path.dirname(os.path.abspath(__file__))
GD = os.path.join(ROOT, "gd_metadata")
REF_GLOB = os.path.join(ROOT, "reference/03_DataPigmentation/*/*/*-DATA-*.json")
OUTDIR = os.path.join(ROOT, "reports/verification")
FRAMES = os.path.join(OUTDIR, "_frames")
NPROMPTS = 16
THUMB_H_MM = 72        # portrait thumbnail height on the page
ROWS_PER_PAGE = 3

# ---------------------------------------------------------------- ffprobe / ffmpeg
def ffprobe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", path],
        capture_output=True, text=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    dur = float(j["format"]["duration"])
    try:
        nframes = int(s.get("nb_frames"))
    except (TypeError, ValueError):
        nframes = round(dur * fps)
    return {"w": s["width"], "h": s["height"], "fps": fps,
            "nframes": nframes, "dur": dur}


def _blackdetect(args):
    """Run ffmpeg blackdetect over a windowed segment; return list of (start,end)."""
    r = subprocess.run(["ffmpeg", *args, "-vf", "blackdetect=d=0.05:pix_th=0.10",
                        "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    iv = []
    for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr):
        iv.append((float(m.group(1)), float(m.group(2))))
    return iv


def content_span(path, dur, head_win=4.0, tail_win=25.0):
    """Return (start, end) trimming leading/trailing black fades (checked in windows)."""
    start, end = 0.0, dur
    if os.path.getsize(path) > 3_000_000_000:   # skip blackdetect on huge share files
        return start, end
    for hs, he in _blackdetect(["-t", str(head_win), "-i", path]):
        if hs <= 0.15:                      # fade-in at the very start
            start = max(start, he)
    # tail: seek to last tail_win seconds; reported times are offsets within the window
    base = max(0.0, dur - tail_win)
    for ts, te in _blackdetect(["-sseof", f"-{tail_win}", "-i", path]):
        abs_end = base + te
        if abs_end >= dur - 0.30:           # fade-out reaching EOF
            end = min(end, base + ts)
    if end - start < 1.0:                   # sanity: never collapse the span
        start, end = 0.0, dur
    return start, end


def extract_frames(path, info, n=NPROMPTS):
    """Extract n frames at fractions i/(n-1) across the non-black span; cache as JPG."""
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(path))
    cdir = os.path.join(FRAMES, key)
    os.makedirs(cdir, exist_ok=True)
    s, e = content_span(path, info["dur"])
    info["content"] = (s, e)
    paths, stamps = [], []
    safe_end = min(e, info["dur"] - 1.5 / max(info["fps"], 1.0))  # avoid seeking past EOF
    for i in range(n):
        frac = i / (n - 1)
        t = s + frac * (e - s)
        t = min(t, safe_end)
        frame = round(t * info["fps"])
        stamps.append((t, frame))
        op = os.path.join(cdir, f"f{i:02d}.jpg")
        if not os.path.exists(op):
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                 "-vf", "scale=-2:760", "-q:v", "3", op],
                capture_output=True, text=True)
        paths.append(op)
    return paths, stamps


# ---------------------------------------------------------------- manifest
def load_refs():
    refs = {}
    for dj in glob.glob(REF_GLOB):
        folder = os.path.dirname(dj)
        sid = re.search(r"-SCE-([A-Z]\d+)-", os.path.basename(dj)).group(1)
        d = json.load(open(dj))
        keys = sorted(d, key=int)
        inp = glob.glob(folder + "/*-INPUT-*.mp4")
        out = glob.glob(folder + "/*-OUTPUT-*.mp4")
        refs[sid] = {"folder": folder, "data": dj,
                     "input": inp[0] if inp else None,
                     "output": out[0] if out else None,
                     "prompts": [d[k]["text"] for k in keys]}
    return refs


# Known source (INPUT / simulation) videos already in the repo for the
# reverse-engineered shots. Artwork (OUTPUT) videos for these, and BOTH videos for the
# generated-from-prompt.json shots (dk01/dm04/dm06/dm08/dm10), are still to be provided:
# drop them in inputs/artworks/ and inputs/sources/ with the shot id in the filename
# (e.g. inputs/artworks/sl02_*.mp4) and rerun -- they will be picked up automatically.
KNOWN_SOURCE = {
    "sl02": "inputs/sl02_OCEAN_01.mp4",
    "sl05": "inputs/sl05_REDWOODS_03_GAN.mp4",
    "sl09": "inputs/sl09_blumina_02.mp4",
    "dk09": "inputs/dk09_biome_lumina.mp4",
    "dm01": "inputs/dm01_rainforest_flowers_01.mp4",
    "dm09": "inputs/dm09_edit_001_blooming_flowers.mp4",
    "dm11": "inputs/dm11_RF_AI_input.mp4",
    "dm13": "inputs/dm13_biome_lumina.mp4",
}
DROP_SOURCES = os.path.join(ROOT, "inputs/sources")
DROP_ARTWORKS = os.path.join(ROOT, "inputs/artworks")

# Explicit source/artwork paths read straight from the read-only shares (no copy / no
# symlink). dm sources are the AI_INPUT videos (U:\); dm artworks are the delivery MOVs
# (U:\...\AI_Sanctuary_EXR\update_010526). Local inputs/ files are used where already
# present. dm13 has no MOV yet (in progress) -> source only.
_DM_AI = "/mnt/ultracache-b/Contributors/Daniel_Mille/AI_INPUT"
_DM_EX = "/mnt/ultracache-b/Contributors/Daniel_Mille/AI_Sanctuary_EXR/update_010526"
EXTRA_PATHS = {
    "dm01": {"source": "inputs/dm01_rainforest_flowers_01.mp4",
             "artwork": f"{_DM_EX}/20260324_gd_dm01_v02_14400f.mov"},
    "dm02": {"source": f"{_DM_AI}/LANDSCAPE_FOOTHILLS_03_30FPS_2048x3072.mov",
             "artwork": f"{_DM_EX}/20260325_gd_dm02_v02_14400f.mov"},
    "dm03": {"source": f"{_DM_AI}/OCEAN_V01_SMOOTH_chf3_rhea1.mp4",
             "artwork": f"{_DM_EX}/20260325_gd_dm03_v02_14400f.mov"},
    "dm04": {"source": f"{_DM_AI}/LANDSCAPE_FOOTHILLS_04_30FPS_2048x3072.mov",
             "artwork": f"{_DM_EX}/20260326_gd_dm04_v02_14400f.mov"},
    "dm05": {"source": f"{_DM_AI}/FLORA_BAY_04_30FPS_2048x3072.mov",
             "artwork": f"{_DM_EX}/20260422_gd_dm05_v03_14400f.mov"},
    "dm06": {"source": f"{_DM_AI}/FLORA_OCEAN_04_30FPS_2048x3072.mov",
             "artwork": f"{_DM_EX}/20260327_gd_dm06_v01_14400f.mov"},
    "dm07": {"source": f"{_DM_AI}/FLORA_REDWOOD_03_30FPS_2048x3072.mov",
             "artwork": f"{_DM_EX}/20260403_gd_dm07_v01_14400f.mov"},
    "dm08": {"source": f"{_DM_AI}/FLORA_FOOTHILLS_02.mp4",
             "artwork": f"{_DM_EX}/20260404_gd_dm08_v01_14400f.mov"},
    "dm09": {"source": "inputs/dm09_edit_001_blooming_flowers.mp4",
             "artwork": f"{_DM_EX}/20260402_gd_dm09_v01_14400f.mov"},
    "dm10": {"source": f"{_DM_AI}/BAY_V01_SMOOTH_chf3_rhea1_prores.mov",
             "artwork": f"{_DM_EX}/20260325_gd_dm10_v02_14400f.mov"},
    "dm11": {"source": "inputs/dm11_RF_AI_input.mp4",
             "artwork": f"{_DM_EX}/20260420_gd_dm11_v01_14400f.mov"},
    "dm12": {"source": f"{_DM_AI}/FLORA_BAY_v02.mp4",
             "artwork": f"{_DM_EX}/20260428_gd_dm12_v01_14400f.mov"},
    "dm13": {"source": "inputs/dm13_biome_lumina.mp4"},
}


def _drop(folder, shot_id):
    hits = sorted(glob.glob(os.path.join(folder, f"*{shot_id}*")))
    hits = [h for h in hits if h.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
    return hits[0] if hits else None


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def resolve_extra(shot_id):
    """Source/artwork videos: explicit override map > drop folders > known sources."""
    ov = EXTRA_PATHS.get(shot_id, {})
    src = _abs(ov["source"]) if ov.get("source") else None
    art = _abs(ov["artwork"]) if ov.get("artwork") else None
    if src and not os.path.exists(src):
        src = None
    if art and not os.path.exists(art):
        art = None
    src = src or _drop(DROP_SOURCES, shot_id)
    art = art or _drop(DROP_ARTWORKS, shot_id)
    if not src and shot_id in KNOWN_SOURCE:
        p = os.path.join(ROOT, KNOWN_SOURCE[shot_id])
        src = p if os.path.exists(p) else None
    return src, art


def build_manifest():
    """For each gd shot: prompts + best reference scene + source/artwork video paths."""
    refs = load_refs()
    shots = []
    for g in sorted(glob.glob(GD + "/*/")):
        name = os.path.basename(g.rstrip("/"))
        dj = glob.glob(g + "*_DATA.json")[0]
        d = json.load(open(dj))
        keys = sorted(d, key=int)
        prompts = [{"key": k, "text": d[k]["text"]} for k in keys]
        ptexts = [p["text"].strip() for p in prompts]
        best, bestn = None, -1
        for sid, r in refs.items():
            n = sum(1 for a, b in zip(ptexts, [t.strip() for t in r["prompts"]])
                    if a == b)
            if n > bestn:
                bestn, best = n, sid
        shot_id = re.search(r"_(sl|dk|dm)\d+", name).group(0).lstrip("_")
        drop_src, drop_art = resolve_extra(shot_id)   # drop folders override everything
        if bestn >= NPROMPTS - 1:           # 15/16 or 16/16 -> copied
            r = refs[best]
            shots.append({"name": name, "shot": shot_id, "data_json": dj,
                          "prompts": prompts, "disposition": "copied",
                          "ref_scene": best, "ref_match": f"{bestn}/16",
                          "source": drop_src or r["input"],
                          "artwork": drop_art or r["output"]})
        else:
            shots.append({"name": name, "shot": shot_id, "data_json": dj,
                          "prompts": prompts,
                          "disposition": "generated / reverse-engineered",
                          "ref_scene": None, "ref_match": f"{bestn}/16 (no match)",
                          "source": drop_src, "artwork": drop_art})
    return shots


# ---------------------------------------------------------------- PDF
def tx(s):
    """Make text safe for fpdf core (latin-1) fonts."""
    if not s:
        return ""
    for a, b in {"—": "-", "–": "-", "’": "'", "‘": "'",
                 "“": '"', "”": '"', "…": "...", " ": " "}.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


def rel(p):
    if not p:
        return "(not provided)"
    r = os.path.relpath(p, ROOT)
    return p if r.startswith("..") else r   # show share/absolute paths in full


DEF_AR = 1396 / 1920  # default portrait aspect for placeholder boxes


def spec_line(info):
    if info is None:
        return "NOT PROVIDED"
    s, e = info.get("content", (0, info["dur"]))
    blk = "" if (s == 0 and abs(e - info["dur"]) < 0.05) \
        else f"   content [{s:.1f}-{e:.1f}]s (black trimmed)"
    return (f"{info['w']}x{info['h']}  {info['fps']:.3f} fps  "
            f"{info['nframes']} frames  {info['dur']:.1f}s{blk}")


def build_pdf(shot, src_info, art_info, src_frames, src_st, art_frames, art_st):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    EPW = pdf.epw  # effective page width

    # ---- header page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 8, shot["name"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    meta = [f"Shot: {shot['shot']}    Disposition: {shot['disposition']}"]
    if shot["ref_scene"]:
        meta.append(f"Reference scene: {shot['ref_scene']}  (prompt match {shot['ref_match']})")
    for line in meta:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Files", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8)
    for label, p in [("PROMPTS (DATA.json)", shot["data_json"]),
                     ("SOURCE  (INPUT mp4)", shot["source"]),
                     ("ARTWORK (OUTPUT mp4)", shot["artwork"])]:
        pdf.multi_cell(0, 4.5, f"{label}: {rel(p)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Video specs", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(0, 4.5, f"SOURCE : {spec_line(src_info)}", new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 4.5, f"ARTWORK: {spec_line(art_info)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "How the 3 resources are lined up", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    note = ("Prompts are on an 8 fps timebase (keys 0,96,...,1440). The 16 prompts are "
            "mapped by NORMALISED position: prompt i -> fraction i/15 of each video's "
            "non-black content. Each row below pairs prompt i with the source frame and "
            "the artwork frame at that same fraction, so the three line up despite "
            "different fps / length. Verify: does the prompt describe what both frames show?")
    pdf.multi_cell(0, 5, note, new_x="LMARGIN", new_y="NEXT")
    if src_info is None or art_info is None:
        miss = " and ".join(x for x, ok in
                            [("SOURCE", src_info), ("ARTWORK", art_info)] if not ok)
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(180, 0, 0)
        pdf.multi_cell(0, 5, f"NOTE: {miss} video not provided -- that column is a "
                             f"placeholder; verify against the other column + prompt.",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    # ---- prompt rows
    img_w_guess = THUMB_H_MM * (src_info["w"] / src_info["h"]) if src_info else THUMB_H_MM * DEF_AR
    art_w_guess = THUMB_H_MM * (art_info["w"] / art_info["h"]) if art_info else THUMB_H_MM * DEF_AR
    col_src_x = pdf.l_margin
    col_art_x = col_src_x + img_w_guess + 4
    col_txt_x = col_art_x + art_w_guess + 4
    txt_w = pdf.w - pdf.r_margin - col_txt_x

    for i, p in enumerate(shot["prompts"]):
        if i % ROWS_PER_PAGE == 0:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_xy(col_src_x, pdf.t_margin)
            pdf.cell(img_w_guess, 5, "SOURCE (input)")
            pdf.set_xy(col_art_x, pdf.t_margin)
            pdf.cell(art_w_guess, 5, "ARTWORK (output)")
            pdf.set_xy(col_txt_x, pdf.t_margin)
            pdf.cell(txt_w, 5, "PROMPT")
            row_top0 = pdf.t_margin + 7
        row = i % ROWS_PER_PAGE
        y = row_top0 + row * (THUMB_H_MM + 6)

        def cell_img(frames, x, w, label):
            if frames is not None:
                pdf.image(frames[i], x=x, y=y, h=THUMB_H_MM)
            else:
                pdf.set_draw_color(180, 180, 180)
                pdf.rect(x, y, w, THUMB_H_MM)
                pdf.set_xy(x, y + THUMB_H_MM / 2 - 4)
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(150, 150, 150)
                pdf.multi_cell(w, 4, f"{label}\nNOT PROVIDED", align="C")
                pdf.set_text_color(0, 0, 0)

        cell_img(src_frames, col_src_x, img_w_guess, "SOURCE")
        cell_img(art_frames, col_art_x, art_w_guess, "ARTWORK")

        key = int(p["key"])
        pdf.set_xy(col_txt_x, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(txt_w, 4.5,
                       f"#{i:02d}  key={key}  (8fps frame {key} = {key/8:.1f}s)",
                       new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(col_txt_x)
        pdf.set_font("Courier", "", 7)
        src_ln = (f"src  t={src_st[i][0]:5.1f}s  frame {src_st[i][1]}/{src_info['nframes']}"
                  if src_frames is not None else "src  NOT PROVIDED")
        art_ln = (f"art  t={art_st[i][0]:5.1f}s  frame {art_st[i][1]}/{art_info['nframes']}"
                  if art_frames is not None else "art  NOT PROVIDED")
        pdf.multi_cell(txt_w, 3.6, src_ln + "\n" + art_ln, new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(col_txt_x)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(txt_w, 4, tx(p["text"]), new_x="LMARGIN", new_y="NEXT")

    os.makedirs(OUTDIR, exist_ok=True)
    op = os.path.join(OUTDIR, shot["name"] + "_VERIFY.pdf")
    pdf.output(op)
    return op


# ---------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    force = "--force" in args                 # rebuild even if the PDF already exists
    want = set(a for a in args if a != "--force")
    shots = build_manifest()
    os.makedirs(FRAMES, exist_ok=True)
    done, exist, empty = [], [], []
    for shot in shots:
        if want and not any(w in shot["name"] for w in want):
            continue
        op = os.path.join(OUTDIR, shot["name"] + "_VERIFY.pdf")
        if os.path.exists(op) and not force:  # never regenerate an existing PDF
            exist.append(shot["name"])
            continue

        def have(p):
            return p and os.path.exists(p)
        si = ffprobe(shot["source"]) if have(shot["source"]) else None
        ai = ffprobe(shot["artwork"]) if have(shot["artwork"]) else None
        if si is None and ai is None:
            # neither video present -> prompt-only PDF still useful, but flag it
            empty.append(shot["name"])
        sf, sst = extract_frames(shot["source"], si) if si else (None, None)
        af, ast = extract_frames(shot["artwork"], ai) if ai else (None, None)
        op = build_pdf(shot, si, ai, sf, sst, af, ast)
        done.append(op)
        tag = "" if (si and ai) else "  [partial: " + \
            ", ".join(x for x, ok in [("no source", si), ("no artwork", ai)] if not ok) + "]"
        print("  built", os.path.relpath(op, ROOT), tag)
    print(f"\nDONE: {len(done)} PDFs built"
          + (f" ({len(empty)} prompt-only)" if empty else ""))
    if exist:
        print(f"KEPT (already built, not regenerated): {len(exist)}")


if __name__ == "__main__":
    main()
