#!/usr/bin/env python
"""
Reverse-engineer house-style prompts from a finished video using Gemini (Vertex AI).

For shots that have neither a reference DATA json nor a source prompt.json (sl02, sl05,
sl09), we sample frames from the delivered 4-minute video at the project's standard
prompt times and ask Gemini to write a single-line "A cinematic ..." prompt for each.

Prompt-time convention (matches reference/03_DataPigmentation):
  prompt_map keys are frame indices on an 8 fps timebase, every 96 frames (= 12 s).
  A 4-minute (240 s) piece therefore has keys 0, 96, ..., 1920  -> 21 prompts.
  The real video frame for a key is round((key / 8) * fps), clamped to the last frame;
  here we seek by timestamp seconds = key / 8.

Output: a minimal prompt file {"prompt_map": {"0": "...", "96": "...", ...}} that the
existing make_metadata_animatediff.py / make_embeddings_exr.py consume unchanged.

Runs in the `gsutil` conda env (has google-genai + vertexai). Reads only local inputs;
never touches /mnt/projects.
"""
import os
import sys
import json
import argparse
import subprocess
import tempfile

from google import genai
from google.genai import types

# --- project constants -------------------------------------------------------
FPS_TIMEBASE = 8          # prompt_map keys are indices on this timebase
KEY_STEP = 96             # one prompt every 96 frames @8fps = every 12 s
DURATION_S = 240          # all final artworks are 4 minutes
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_PROJECT = "ras-ai-dev"
DEFAULT_LOCATION = "us-central1"

# A near-black frame has mean luma below this (0-255). Reported to the user.
BLACK_MEAN_THRESHOLD = 6.0

# Keys used by the AnimateDiff source videos (and the copied reference DATA jsons):
# 16 keyframes on the 8 fps timebase. Use --match-animatediff to emit these instead of
# the full 4-minute 0..1920 grid, dropping black frames and scaling content to fit.
ANIMATEDIFF_KEYS = list(range(0, 1441, KEY_STEP))  # [0, 96, ..., 1440], 16 keys

# Diverse house-style examples (mix of shot types) so output isn't biased to landscape.
STYLE_EXAMPLES = [
    "A cinematic close-up of bright pink coralline algae growing along a rocky reef, "
    "with golden kelp blades swaying in the current and soft turquoise water reflecting sunlight.",
    "A cinematic landscape of California foothills, with golden rolling hills dotted with "
    "clusters of green succulents, vibrant wildflowers in orange and yellow, and soft grasses "
    "shimmering under a bright, cloudless midday sky.",
    "A cinematic underwater view in a shallow sunlit area: clear blue water glows with "
    "shimmering silver light patterns from above, while golden sunbeams penetrate downwards "
    "towards a rocky seabed with sandy patches.",
]

INSTRUCTION = (
    "You are writing image-generation prompts for a nature art project. Look at the frame "
    "and write ONE single-line prompt describing exactly what is shown.\n"
    "Rules:\n"
    "  - The prompt MUST begin with the words 'A cinematic '.\n"
    "  - Choose the shot type that actually fits the frame (close-up, macro, underwater, "
    "landscape, aerial, etc.). Do NOT default to 'landscape'.\n"
    "  - Describe the real subject, colors, lighting and setting concretely, in one sentence.\n"
    "  - If the frame is solid black or essentially empty, respond with EXACTLY: "
    "'A cinematic solid black frame.'\n"
    "  - Output only the prompt sentence, no quotes, no preamble.\n\n"
    "Examples of the house style:\n- " + "\n- ".join(STYLE_EXAMPLES)
)


def keys_for_duration(duration_s=DURATION_S):
    last = duration_s * FPS_TIMEBASE  # e.g. 240 * 8 = 1920
    return list(range(0, last + 1, KEY_STEP))


def probe_fps_dur(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate:format=duration",
         "-of", "json", video],
        capture_output=True, text=True, check=True,
    ).stdout
    info = json.loads(out)
    num, den = info["streams"][0]["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    dur = float(info["format"]["duration"])
    return fps, dur


def detect_content_window(video, dur):
    """Use ffmpeg blackdetect to find the non-black content window [start, end].

    Drops a leading black segment (if any) and a trailing black segment (the fade-out),
    so generated prompts never describe black frames. Returns (start, end, intervals).
    """
    res = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", video,
         "-vf", "blackdetect=d=0.05:pix_th=0.05", "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    intervals = []
    for line in res.stderr.splitlines():
        if "black_start:" in line and "black_end:" in line:
            try:
                s = float(line.split("black_start:")[1].split()[0])
                e = float(line.split("black_end:")[1].split()[0])
                intervals.append((s, e))
            except (ValueError, IndexError):
                pass
    # Margin so the boundary samples sit clearly inside non-black content, not on the
    # fade edge where blackdetect's threshold is first crossed.
    margin = 0.3
    start, end = 0.0, dur
    for s, e in intervals:
        if s <= 0.5:            # leading black -> push content start past it
            start = max(start, e + margin)
        if e >= dur - 0.5:      # trailing black (fade-out) -> pull content end before it
            end = min(end, s - margin)
    return start, end, intervals


def extract_frame(video, t_seconds, out_path, fps, dur):
    """Extract a single frame at t_seconds, clamped to the last real frame."""
    # 1.5-frame margin: lands safely inside the final frame despite fp/seek rounding.
    last_frame_t = dur - (1.5 / fps)
    t = max(0.0, min(t_seconds, last_frame_t))
    subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-y",
         "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "2", out_path],
        check=True,
    )


def frame_mean_luma(path):
    """Mean luma (0-255) via ffmpeg signalstats+metadata print; for black detection."""
    res = subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "info", "-i", path,
         "-vf", "signalstats,metadata=print", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    # metadata=print emits lines like "lavfi.signalstats.YAVG=3.210000"
    for line in res.stderr.splitlines():
        idx = line.find("signalstats.YAVG=")
        if idx != -1:
            try:
                return float(line[idx + len("signalstats.YAVG="):].split()[0])
            except (ValueError, IndexError):
                return None
    return None


def gemini_prompt_for(client, model, img_path):
    data = open(img_path, "rb").read()
    resp = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=data, mime_type="image/jpeg"),
            INSTRUCTION,
        ],
    )
    return (resp.text or "").strip().replace("\n", " ").strip()


def main():
    ap = argparse.ArgumentParser(description="Reverse-engineer prompts from a video via Gemini.")
    ap.add_argument("video", help="Path to the local input video (e.g. inputs/sl02_OCEAN_01.mp4)")
    ap.add_argument("-o", "--output", required=True, help="Output prompt json path")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--project", default=DEFAULT_PROJECT)
    ap.add_argument("--location", default=DEFAULT_LOCATION)
    ap.add_argument("--duration", type=float, default=DURATION_S)
    ap.add_argument("--match-animatediff", action="store_true",
                    help="Emit the 16 AnimateDiff keys (0..1440), drop black frames, and "
                         "scale the non-black content evenly across those keys.")
    args = ap.parse_args()

    if "/mnt/projects" in os.path.abspath(args.video):
        sys.exit("Refusing to read from /mnt/projects.")

    fps, dur = probe_fps_dur(args.video)

    # Build the list of (key, sample_time_seconds) pairs.
    if args.match_animatediff:
        keys = ANIMATEDIFF_KEYS
        cstart, cend, intervals = detect_content_window(args.video, dur)
        n = len(keys)
        samples = [(k, cstart + (i / (n - 1)) * (cend - cstart)) for i, k in enumerate(keys)]
        print(f"[{os.path.basename(args.video)}] fps={fps:.3f}  match-animatediff: "
              f"{n} keys {keys[0]}..{keys[-1]}; content [{cstart:.2f},{cend:.2f}]s "
              f"(black intervals: {intervals or 'none'})")
    else:
        keys = keys_for_duration(int(args.duration))
        samples = [(k, k / FPS_TIMEBASE) for k in keys]
        print(f"[{os.path.basename(args.video)}] fps={fps:.3f}  {len(keys)} prompts "
              f"(keys {keys[0]}..{keys[-1]} step {KEY_STEP})")

    client = genai.Client(vertexai=True, project=args.project, location=args.location)

    prompt_map = {}
    black_keys = []
    with tempfile.TemporaryDirectory() as td:
        for key, t in samples:
            fpath = os.path.join(td, f"{key:05d}.jpg")
            extract_frame(args.video, t, fpath, fps, dur)

            luma = frame_mean_luma(fpath)
            is_black = luma is not None and luma < BLACK_MEAN_THRESHOLD

            text = gemini_prompt_for(client, args.model, fpath)
            if not text.startswith("A cinematic"):
                text = "A cinematic " + text[0].lower() + text[1:] if text else "A cinematic frame."
            prompt_map[str(key)] = text

            flag = "  <-- BLACK FRAME" if is_black else ""
            print(f"  key {key:>4} (t={t:6.1f}s, luma={luma}): {text[:80]}{flag}")
            if is_black:
                black_keys.append(key)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({"prompt_map": prompt_map}, f, indent=2)
    print(f"Wrote {args.output}  ({len(prompt_map)} prompts)")

    if black_keys:
        print(f"!! BLACK FRAMES still present at sampled keys: {black_keys}")
    return black_keys


if __name__ == "__main__":
    main()
