import os, sys
import json
import glob
import argparse

from diffusers import StableDiffusionPipeline
import torch

def make_reverse_token_dict():
    tokens_path = "data/vocab.json"
    with open(tokens_path, 'r') as f:
        text2token = json.load(f)

    token2text = {}
    for text, token in text2token.items():
        token2text[token] = text
    return token2text

def process_prompt_json(data, pipe, token2text):
    """Build result dict from data['prompt_map'] using pipe tokenizer."""
    result = {}
    prompt_map = data["prompt_map"]
    for idx in prompt_map:
        prompt = prompt_map[idx]
        tok_int = pipe.tokenizer(prompt)["input_ids"]
        tok_txt = [token2text[tok] for tok in tok_int]
        result[idx] = {
            "text": prompt,
            "tokens_int": tok_int,
            "tokens_text": tok_txt,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="Build AnimateDiff metadata from prompt JSON.")
    parser.add_argument(
        "input_json",
        nargs="?",
        default=None,
        help="Path to prompt JSON (e.g. inputs/wef_orange_flower_prompt.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output path for metadata JSON (default: results/<input_basename>_metadata.json)",
    )
    args = parser.parse_args()

    # Tokens prep
    token2text = make_reverse_token_dict()
    model_id = "sd-legacy/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to(os.environ.get("DEVICE", "cuda"))

    if args.input_json is not None:
        # Single-file mode: use the given input JSON
        input_path = args.input_json
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        with open(input_path, "r") as f:
            data = json.load(f)
        result = process_prompt_json(data, pipe, token2text)
        if args.output:
            save_path = args.output
        else:
            save_dir = "results"
            os.makedirs(save_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(input_path))[0]
            save_path = os.path.join(save_dir, f"{base}_metadata.json")
        with open(save_path, "w") as f:
            json.dump(result, f, indent=4)
        print(f"Saved {save_path}")
        return

    # Legacy: hardcoded folder loop
    save_dir = "results"
    MAKE_PROMPT = False
    server_dir = "/mnt/projects/Biophilia - Google Gradient Canopy/Team/HyeMin/FLUID_SIM_BASE_ANIMATEDIFF"
    categories = ["FLORA", "FAUNA", "LANDSCAPE"]
    biomes = ["BAY", "FOOTHILLS", "REDWOOD", "OCEAN"]

    for ct in categories:
        for bm in biomes:
            num_vers = 4 if ct != "FAUNA" else 1
            for ver in range(num_vers):
                result = {}
                title = f"{ct}_{bm}_{ver+1:02d}"
                save_file_name = title + "_metadata_prompt.json"
                save_file_dir = os.path.join(save_dir, ct, bm)
                os.makedirs(save_file_dir, exist_ok=True)
                save_path = os.path.join(save_file_dir, save_file_name)

                if MAKE_PROMPT:
                    ver_name = f"V{ver+1:02d}"
                    json_path = None
                    for vn in [ver_name, ver_name + "_SMOOTH", ver_name + "_ORIGINAL"]:
                        json_path = os.path.join(server_dir, ct, bm, vn)
                        if os.path.exists(json_path):
                            break
                    if json_path is None:
                        raise ValueError(f"Can't find metadata dir for {json_path}")
                    filenames = glob.glob(os.path.join(json_path, "*/prompt.json"))
                    if len(filenames) != 1:
                        raise ValueError(f"Trouble locating metadata for {json_path}")
                    with open(filenames[0], "r") as f:
                        data = json.load(f)
                else:
                    with open(save_path, "r") as f:
                        data = json.load(f)

                result = process_prompt_json(data, pipe, token2text)
                with open(save_path, "w") as f:
                    json.dump(result, f, indent=4)
                print(f"Saved {save_path}")



if __name__ == "__main__":
    main()
