import os, sys
import json
import glob
import argparse

import OpenEXR
import Imath
import numpy as np

from diffusers import StableDiffusionPipeline
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import torch

def lerp(a, b, alpha):
    return (b - a) * alpha + a

class PromptEncoder:
    def __init__(
            self,
            pipe,
            device,
            latents_device,
            num_videos_per_prompt,
            do_classifier_free_guidance,
            region_condi_list,
            negative_prompt,
            is_signle_prompt_mode,
            clip_skip,
            multi_uncond_mode
        ):
        self.pipe = pipe
        self.is_single_prompt_mode=is_signle_prompt_mode
        self.do_classifier_free_guidance = do_classifier_free_guidance

        uncond_num = 0
        if do_classifier_free_guidance:
            if multi_uncond_mode:
                uncond_num = len(region_condi_list)
            else:
                uncond_num = 1

        ### text

        prompt_nums = []
        prompt_map_list = []
        prompt_list = []

        for condi in region_condi_list:
            _prompt_map = condi["prompt_map"]
            prompt_map_list.append(_prompt_map)
            _prompt_map = dict(sorted(_prompt_map.items()))
            _prompt_list = [_prompt_map[key_frame] for key_frame in _prompt_map.keys()]
            prompt_nums.append( len(_prompt_list) )
            prompt_list += _prompt_list

        if isinstance(negative_prompt, str):
            negative_prompt = [negative_prompt] * len(prompt_list)
        prompt_embeds = pipe._encode_prompt(
            prompt_list,
            device,
            num_videos_per_prompt,
            do_classifier_free_guidance,
            negative_prompt,
            prompt_embeds=None,
            negative_prompt_embeds=None,
            clip_skip=clip_skip,
        ).to(device = latents_device)

        self.prompt_embeds_dtype = prompt_embeds.dtype


        if do_classifier_free_guidance:
            negative, positive = prompt_embeds.chunk(2, 0)
            negative = negative.chunk(negative.shape[0], 0)
            positive = positive.chunk(positive.shape[0], 0)
        else:
            positive = prompt_embeds
            positive = positive.chunk(positive.shape[0], 0)

        # if pipe.ip_adapter:
        #     pipe.ip_adapter.set_text_length(positive[0].shape[1])


        prompt_embeds_region_list = []

        if do_classifier_free_guidance:
            prompt_embeds_region_list = [
                {
                    0:negative[0]
                }
            ] * uncond_num + prompt_embeds_region_list

        pos_index = 0
        for prompt_map, num in zip(prompt_map_list, prompt_nums):
            prompt_embeds_map={}
            pos = positive[pos_index:pos_index+num]

            for i, key_frame in enumerate(prompt_map):
                prompt_embeds_map[key_frame] = pos[i]

            prompt_embeds_region_list.append( prompt_embeds_map )
            pos_index += num

        if do_classifier_free_guidance:
            prompt_map_list = [
                {
                    0:negative_prompt
                }
            ] * uncond_num + prompt_map_list

        self.prompt_map_list = prompt_map_list
        self.prompt_embeds_region_list = prompt_embeds_region_list

        ### image
        # if pipe.ip_adapter:
        #
        #     ip_im_nums = []
        #     ip_im_map_list = []
        #     ip_im_list = []
        #
        #     for condi in region_condi_list:
        #         _ip_im_map = condi["ip_adapter_map"]["images"]
        #         ip_im_map_list.append(_ip_im_map)
        #         _ip_im_map = dict(sorted(_ip_im_map.items()))
        #         _ip_im_list = [_ip_im_map[key_frame] for key_frame in _ip_im_map.keys()]
        #         ip_im_nums.append( len(_ip_im_list) )
        #         ip_im_list += _ip_im_list
        #
        #     positive, negative = pipe.ip_adapter.get_image_embeds(ip_im_list)
        #
        #     positive = positive.to(device=latents_device)
        #     negative = negative.to(device=latents_device)
        #
        #     bs_embed, seq_len, _ = positive.shape
        #     positive = positive.repeat(1, 1, 1)
        #     positive = positive.view(bs_embed * 1, seq_len, -1)
        #
        #     bs_embed, seq_len, _ = negative.shape
        #     negative = negative.repeat(1, 1, 1)
        #     negative = negative.view(bs_embed * 1, seq_len, -1)
        #
        #     if do_classifier_free_guidance:
        #         negative = negative.chunk(negative.shape[0], 0)
        #         positive = positive.chunk(positive.shape[0], 0)
        #     else:
        #         positive = positive.chunk(positive.shape[0], 0)
        #
        #     im_prompt_embeds_region_list = []
        #
        #     if do_classifier_free_guidance:
        #         im_prompt_embeds_region_list = [
        #             {
        #                 0:negative[0]
        #             }
        #         ] * uncond_num + im_prompt_embeds_region_list
        #
        #     pos_index = 0
        #     for ip_im_map, num in zip(ip_im_map_list, ip_im_nums):
        #         im_prompt_embeds_map={}
        #         pos = positive[pos_index:pos_index+num]
        #
        #         for i, key_frame in enumerate(ip_im_map):
        #             im_prompt_embeds_map[key_frame] = pos[i]
        #
        #         im_prompt_embeds_region_list.append( im_prompt_embeds_map )
        #         pos_index += num
        #
        #
        #     if do_classifier_free_guidance:
        #         ip_im_map_list = [
        #             {
        #                 0:None
        #             }
        #         ] * uncond_num + ip_im_map_list
        #
        #
        #     self.ip_im_map_list = ip_im_map_list
        #     self.im_prompt_embeds_region_list = im_prompt_embeds_region_list


    def _get_current_prompt_embeds_from_text(
            self,
            prompt_map,
            prompt_embeds_map,
            center_frame = None,
            video_length : int = 0
            ):

        key_prev = list(prompt_map.keys())[-1]
        key_next = list(prompt_map.keys())[0]

        for p in prompt_map.keys():
            if p > center_frame:
                key_next = p
                break
            key_prev = p

        dist_prev = center_frame - key_prev
        if dist_prev < 0:
            dist_prev += video_length
        dist_next = key_next - center_frame
        if dist_next < 0:
            dist_next += video_length

        if key_prev == key_next or dist_prev + dist_next == 0:
            return prompt_embeds_map[key_prev]

        rate = dist_prev / (dist_prev + dist_next)

        return lerp( prompt_embeds_map[key_prev], prompt_embeds_map[key_next], rate )

    def get_current_prompt_embeds_from_text(
            self,
            center_frame = None,
            video_length : int = 0
            ):
        outputs = ()
        for prompt_map, prompt_embeds_map in zip(self.prompt_map_list, self.prompt_embeds_region_list):
            embs = self._get_current_prompt_embeds_from_text(
                prompt_map,
                prompt_embeds_map,
                center_frame,
                video_length)
            outputs += (embs,)

        return outputs

    def _get_current_prompt_embeds_from_image(
            self,
            ip_im_map,
            im_prompt_embeds_map,
            center_frame = None,
            video_length : int = 0
            ):

        key_prev = list(ip_im_map.keys())[-1]
        key_next = list(ip_im_map.keys())[0]

        for p in ip_im_map.keys():
            if p > center_frame:
                key_next = p
                break
            key_prev = p

        dist_prev = center_frame - key_prev
        if dist_prev < 0:
            dist_prev += video_length
        dist_next = key_next - center_frame
        if dist_next < 0:
            dist_next += video_length

        if key_prev == key_next or dist_prev + dist_next == 0:
            return im_prompt_embeds_map[key_prev]

        rate = dist_prev / (dist_prev + dist_next)

        return get_tensor_interpolation_method()( im_prompt_embeds_map[key_prev], im_prompt_embeds_map[key_next], rate)

    def get_current_prompt_embeds_from_image(
            self,
            center_frame = None,
            video_length : int = 0
            ):
        outputs=()
        for prompt_map, prompt_embeds_map in zip(self.ip_im_map_list, self.im_prompt_embeds_region_list):
            embs = self._get_current_prompt_embeds_from_image(
                prompt_map,
                prompt_embeds_map,
                center_frame,
                video_length)
            outputs += (embs,)

        return outputs

    def get_current_prompt_embeds_single(
            self,
            context: List[int] = None,
            video_length : int = 0
            ):
        center_frame = context[len(context)//2]
        text_emb = self.get_current_prompt_embeds_from_text(center_frame, video_length)
        text_emb = torch.cat(text_emb)
        # if self.pipe.ip_adapter:
        #     image_emb = self.get_current_prompt_embeds_from_image(center_frame, video_length)
        #     image_emb = torch.cat(image_emb)
        #     return torch.cat([text_emb,image_emb], dim=1)
        # else:
        return text_emb

    def get_current_prompt_embeds_multi(
            self,
            context: List[int] = None,
            video_length : int = 0
            ):

        emb_list = []
        for c in context:
            t = self.get_current_prompt_embeds_from_text(c, video_length)
            for i, emb in enumerate(t):
                if i >= len(emb_list):
                    emb_list.append([])
                emb_list[i].append(emb)
        # NOTE : should be done in tensor operations in a simple way.. so convoluted

        # emb_list has len 2
        # each elem of emb_list has len 16

        text_emb = []
        for emb in emb_list:
            emb = torch.cat(emb)  # first cat dim len 16
            text_emb.append(emb)
        text_emb = torch.cat(text_emb)  # them cat dim len 2

        # if self.pipe.ip_adapter == None:
        return text_emb
        #
        # emb_list = []
        # for c in context:
        #     t = self.get_current_prompt_embeds_from_image(c, video_length)
        #     for i, emb in enumerate(t):
        #         if i >= len(emb_list):
        #             emb_list.append([])
        #         emb_list[i].append(emb)
        #
        # image_emb = []
        # for emb in emb_list:
        #     emb = torch.cat(emb)
        #     image_emb.append(emb)
        # image_emb = torch.cat(image_emb)
        #
        # return torch.cat([text_emb,image_emb], dim=1)
        #
    def get_current_prompt_embeds(
            self,
            context: List[int] = None,
            video_length : int = 0
            ):
        return self.get_current_prompt_embeds_single(context,video_length) if self.is_single_prompt_mode else self.get_current_prompt_embeds_multi(context,video_length)

    def get_prompt_embeds_dtype(self):
        return self.prompt_embeds_dtype

    def get_condi_size(self):
        return len(self.prompt_embeds_region_list)

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

def _prompt_map_from_data(data):
    """Build prompt_map from either prompt_map format or metadata format."""
    if "prompt_map" in data:
        return {int(k): v for k, v in data["prompt_map"].items()}
    return {int(k): data[k]["text"] for k in data}


def main():
    parser = argparse.ArgumentParser(description="Build prompt embeddings EXR from prompt JSON.")
    parser.add_argument(
        "input_json",
        nargs="?",
        default=None,
        help="Path to prompt JSON (e.g. inputs/wef_orange_flower_prompt.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output EXR path (default: results/PROMPT_EMBEDDINGS/<input_basename>_prompt_embeddings_combined.exr)",
    )
    args = parser.parse_args()

    save_dir = "results"
    device = os.environ.get("DEVICE", "cuda")
    model_id = "sd-legacy/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
    pipe = pipe.to(device)
    negative_prompt = "worst quality, low quality, nsfw, logo"

    if args.input_json is not None:
        input_path = args.input_json
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        with open(input_path, "r") as f:
            data = json.load(f)
        prompt_map = _prompt_map_from_data(data)
        region_condi_list = [{"prompt_map": prompt_map, "ip_adapter_map": None}]
        prompt_encoder = PromptEncoder(
            pipe,
            device,
            device,
            1,
            True,
            region_condi_list,
            negative_prompt,
            False,
            1,
            False,
        )
        comb_embeds_list = [
            prompt_encoder.get_current_prompt_embeds([int(key)], 1).detach().cpu().numpy()
            for key in sorted(prompt_map.keys(), key=int)
        ]
        comb_embeds = np.concatenate(comb_embeds_list, axis=1)
        if args.output:
            output_path = args.output
        else:
            os.makedirs("results/PROMPT_EMBEDDINGS", exist_ok=True)
            base = os.path.splitext(os.path.basename(input_path))[0]
            output_path = f"results/PROMPT_EMBEDDINGS/{base}_prompt_embeddings_combined.exr"
        write_two_channel_exr_from_matrix(comb_embeds, output_path, channel_names=("R", "G"))
        print(f"Wrote {output_path}")
        return

    # Legacy: hardcoded folder loop
    categories = ["FLORA", "FAUNA", "LANDSCAPE"]
    biomes = ["BAY", "FOOTHILLS", "REDWOOD", "OCEAN"]

    for ct in categories:
        for bm in biomes:
            num_vers = 4 if ct != "FAUNA" else 1
            for ver in range(num_vers):
                title = f"{ct}_{bm}_{ver+1:02d}"
                save_file_name = title + "_metadata_prompt.json"
                save_file_dir = os.path.join(save_dir, ct, bm)
                os.makedirs(save_file_dir, exist_ok=True)
                save_path = os.path.join(save_file_dir, save_file_name)

                with open(save_path, "r") as f:
                    data = json.load(f)

                region_condi_list = [{"prompt_map": {int(key): data[key]["text"] for key in data}, "ip_adapter_map": None}]
                prompt_encoder = PromptEncoder(
                    pipe,
                    device,
                    device,
                    1,
                    True,
                    region_condi_list,
                    negative_prompt,
                    False,
                    1,
                    False,
                )

                comb_embeds_list = [
                    prompt_encoder.get_current_prompt_embeds([int(key)], 1).detach().cpu().numpy()
                    for key in data
                ]
                comb_embeds = np.concatenate(comb_embeds_list, axis=1)
                output_file_custom = f"results/PROMPT_EMBEDDINGS/{title}_prompt_embeddings_combined.exr"
                os.makedirs("results/PROMPT_EMBEDDINGS", exist_ok=True)
                write_two_channel_exr_from_matrix(comb_embeds, output_file_custom, channel_names=("R", "G"))
                print(f"Wrote {output_file_custom}")

                # # Tokens
                # for idx in prompt_map:
                #     prompt = prompt_map[idx]
                #     tok_int = pipe.tokenizer(prompt)['input_ids']
                #     tok_txt = [token2text[tok] for tok in tok_int]
                #     result[idx] = {
                #         "text" : prompt,
                #         "tokens_int" : tok_int,
                #         "tokens_text" : tok_txt
                #     }



if __name__ == "__main__":
    main()
