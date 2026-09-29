#!/usr/bin/env python3
import yaml
import os

def verify_prompt_count(yaml_file_path, expected_count=12):
    """
    Verifies the number of prompts in a YAML file.
    """
    try:
        with open(yaml_file_path, 'r') as f:
            # Handle empty file case
            content = f.read()
            if not content.strip():
                print(f"INFO: '{os.path.basename(yaml_file_path)}' is empty.")
                return

            # Go back to the beginning of the file to read yaml
            f.seek(0)
            data = yaml.safe_load(f)

        if data and 'prompt' in data and isinstance(data['prompt'], list):
            prompt_count = len(data['prompt'])
            if prompt_count == expected_count:
                print(f"OK: '{os.path.basename(yaml_file_path)}' has {prompt_count} entries.")
            else:
                print(f"FAIL: '{os.path.basename(yaml_file_path)}' has {prompt_count} entries, but expected {expected_count}.")
        else:
            print(f"INFO: '{os.path.basename(yaml_file_path)}' is not empty but has no 'prompt' list.")

    except yaml.YAMLError as e:
        print(f"ERROR: Could not parse YAML in '{os.path.basename(yaml_file_path)}': {e}")
    except Exception as e:
        print(f"ERROR: Could not process '{os.path.basename(yaml_file_path)}': {e}")

def main():
    prompts_dir = "prompts"
    
    # Get a sorted list of YAML files
    try:
        files = sorted([f for f in os.listdir(prompts_dir) if f.endswith('.yaml')])
    except FileNotFoundError:
        print(f"ERROR: Directory not found at '{prompts_dir}'")
        return
        
    if not files:
        print("No YAML files found in the 'prompts' directory.")
        return

    print("Verifying prompt counts in YAML files...\n")
    for filename in files:
        yaml_file_path = os.path.join(prompts_dir, filename)
        verify_prompt_count(yaml_file_path)

    print("\nVerification complete.")

if __name__ == "__main__":
    main() 