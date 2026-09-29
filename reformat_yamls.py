#!/usr/bin/env python3
import yaml
import os

def reformat_yaml_file(yaml_file_path):
    """
    Reformats a YAML file to ensure prompts are on single lines and properly indented.
    """
    try:
        with open(yaml_file_path, 'r') as f:
            content = f.read()
            if not content.strip():
                print(f"INFO: '{os.path.basename(yaml_file_path)}' is empty, skipping.")
                return

            f.seek(0)
            data = yaml.safe_load(f)

        if data and 'prompt' in data and isinstance(data['prompt'], list):
            # The PyYAML library handles indentation correctly by default.
            # To prevent line wrapping of long strings, we use the 'width' parameter.
            with open(yaml_file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=False, width=float('inf'))
            print(f"Reformatted: {os.path.basename(yaml_file_path)}")
        else:
            print(f"INFO: No 'prompt' list found in '{os.path.basename(yaml_file_path)}', skipping.")

    except Exception as e:
        print(f"ERROR: Could not process '{os.path.basename(yaml_file_path)}': {e}")

def main():
    prompts_dir = "prompts"
    files_to_reformat = [
        "biomes4_A_selects.yaml",
        "biomes4_B_selects.yaml",
        "biomes4_C_selects.yaml",
        "biomes4_D_selects.yaml",
    ]

    print("Reformatting specified YAML files...\n")
    for filename in files_to_reformat:
        yaml_file_path = os.path.join(prompts_dir, filename)
        if os.path.exists(yaml_file_path):
            reformat_yaml_file(yaml_file_path)
        else:
            print(f"WARNING: File not found: {yaml_file_path}")

    print("\nReformatting complete.")

if __name__ == "__main__":
    main() 