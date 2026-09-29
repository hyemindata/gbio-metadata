import os
import yaml
import json
import glob

import numpy as np
import OpenEXR
import Imath

import torch
from diffusers import StableCascadeDecoderPipeline, StableCascadePriorPipeline

def write_two_channel_exr_from_matrix(matrix, output_filename="output_2channel.exr", channel_names=('R', 'G')):
    """
    Writes a [2, H, W] NumPy matrix as an EXR image with two specified channels.

    Args:
        matrix (numpy.ndarray): Input matrix of shape [2, H, W] and dtype float32.
                                The first slice matrix[0] will be the first channel,
                                matrix[1] will be the second channel.
        output_filename (str): Name of the EXR file to save.
        channel_names (tuple): A tuple of two strings for the channel names (e.g., ('R', 'G')).
                               Standard names are 'R', 'G', 'B', 'A', 'Z'.
                               You can also use custom names like 'motionX', 'motionY'.
    """
    if not isinstance(matrix, np.ndarray):
        raise TypeError("Input matrix must be a NumPy array.")
    if matrix.ndim != 3 or matrix.shape[0] != 2:
        raise ValueError(f"Input matrix must have shape [2, H, W], got {matrix.shape}")
    if matrix.dtype != np.float32:
        print(f"Warning: Input matrix dtype is {matrix.dtype}, converting to float32.")
        matrix = matrix.astype(np.float32)
    if len(channel_names) != 2 or not all(isinstance(name, str) for name in channel_names):
        raise ValueError("channel_names must be a tuple of two strings.")

    _, height, width = matrix.shape # e.g., matrix.shape = (2, 77, 768) -> height=77, width=768

    # Prepare data for each channel
    data_ch1 = matrix[0, :, :].tobytes()
    data_ch2 = matrix[1, :, :].tobytes()

    # Create EXR header
    header = OpenEXR.Header(width, height) # Resolution is width x height
    
    pixel_type = Imath.PixelType(Imath.PixelType.FLOAT) # For 32-bit float

    header['channels'] = {
        channel_names[0]: Imath.Channel(pixel_type),
        channel_names[1]: Imath.Channel(pixel_type)
    }
    
    # Optional: Set compression
    # header['compression'] = Imath.Compression(Imath.Compression.ZIP_COMPRESSION)

    try:
        exr_file = OpenEXR.OutputFile(output_filename, header)
        exr_file.writePixels({
            channel_names[0]: data_ch1,
            channel_names[1]: data_ch2
        })
    except Exception as e:
        print(f"Error writing EXR file '{output_filename}': {e}")
    finally:
        if 'exr_file' in locals() and exr_file:
            exr_file.close()
            print(f"Successfully wrote '{output_filename}' with channels {channel_names} ({width}x{height}, 32-bit float).")


def make_reverse_token_dict():
    tokens_path = "./models/stable-cascade-prior/tokenizer/vocab.json"
    with open(tokens_path, 'r') as f:
        text2token = json.load(f)

    token2text = {}
    for text, token in text2token.items():
        token2text[token] = text
    return token2text

def read_yaml_to_dict(file_path):
    with open(file_path, 'r') as file:
        try:
            yaml_data = yaml.safe_load(file)
            return yaml_data
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
            return None

def main():
    prompts_dir = "./prompts"  # Changed to local prompts directory

    token2text = make_reverse_token_dict()

    prior = StableCascadePriorPipeline.from_pretrained("./models/stable-cascade-prior", variant="bf16", torch_dtype=torch.bfloat16)
    prior.to("cuda")

    # Get all YAML files in the prompts directory
    yaml_files = glob.glob(os.path.join(prompts_dir, "*_PRT.yaml"))
    
    negative_prompt = "ugly, blurry, low quality"

    for yaml_file in yaml_files:
        # Extract the base name without extension for the output filename
        base_name = os.path.splitext(os.path.basename(yaml_file))[0]
        save_name = f"results/CHAPTER_LATENTBLENDING/{base_name}.json"
        
        # Read the YAML file
        data_dict = read_yaml_to_dict(yaml_file)
        if data_dict is None:
            print(f"Failed to read {yaml_file}, skipping...")
            continue
            
        prompts = data_dict.get('prompt', [])
        if not prompts:
            # Try alternative keys for prompts
            alternative_keys = ['prompts', 'text', 'description', 'caption', 'content']
            for key in alternative_keys:
                prompts = data_dict.get(key, [])
                if prompts:
                    print(f"Found prompts under key '{key}' in {yaml_file}")
                    break
            
            # If still no prompts, try to generate a default prompt from filename
            if not prompts:
                base_name = os.path.splitext(os.path.basename(yaml_file))[0]
                # Remove common suffixes and convert to readable text
                default_prompt = base_name.replace('_PRT', '').replace('_', ' ').strip()
                if default_prompt:
                    prompts = [default_prompt]
                    print(f"Generated default prompt from filename: '{default_prompt}' for {yaml_file}")
                else:
                    print(f"No prompts found in {yaml_file} and could not generate default prompt, skipping...")
                    continue

        results = {}
        prompt_encode_list = []
        
        for idx, pt in enumerate(prompts):
            tokens = prior.tokenizer(pt)
            attn_mask = tokens['attention_mask']
            int_tokens = tokens['input_ids']
            text_tokens = [token2text[elem] for elem in int_tokens]

            results[str(idx)] = {
                'text' : pt,
                'tokens_int' : int_tokens,
                'tokens_text' : text_tokens
            }

            print(f"Processing prompt {idx + 1}/{len(prompts)}: {pt[:50]}...")
            
            # clip_tokens_unpooled = prior.tokenizer([pt, negative_prompt], truncation=True, padding="max_length",
            clip_tokens_unpooled = prior.tokenizer([negative_prompt, pt], truncation=True, padding="max_length",
                                        max_length=prior.tokenizer.model_max_length,
                                        return_tensors="pt").to("cuda")
            text_encoder_output = prior.text_encoder(**clip_tokens_unpooled, output_hidden_states=True)

            prompt_encode = text_encoder_output.hidden_states[-1]

            prompt_encode_list.append(prompt_encode.to(torch.float32).clone().detach().cpu().numpy())

        # Save the results JSON
        os.makedirs(os.path.dirname(save_name), exist_ok=True)
        with open(save_name, 'w') as f:
            json.dump(results, f, indent=4)

        # Create and save the embeddings EXR file
        if prompt_encode_list:
            comb_embeds = np.concatenate(prompt_encode_list, axis=1)
            exr_filename = save_name.replace('_PRT.json', '_EMB.exr')
            write_two_channel_exr_from_matrix(comb_embeds, output_filename=exr_filename)
            print(f"Saved {save_name} and {exr_filename}.")
        else:
            print(f"No embeddings generated for {yaml_file}.")

if __name__ == "__main__":
    main()
