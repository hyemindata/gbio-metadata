#!/usr/bin/env python3
import yaml
import os

def process_yaml_file(yaml_file_path):
    """
    Process YAML file to remove duplicate last entry and ensure 12 entries
    """
    # Read YAML file
    with open(yaml_file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # If the file is empty, do nothing
    if not data or 'prompt' not in data or not isinstance(data['prompt'], list):
        print(f"Skipping empty or invalid file: {yaml_file_path}")
        return
    
    prompts = data['prompt']
    
    # Check if there are more than 12 entries
    if len(prompts) > 12:
        # Check if the last entry is a duplicate of the first
        if prompts[0] == prompts[-1]:
            prompts.pop()
            print(f"Removed duplicate last entry from: {yaml_file_path}")
    
    # Ensure there are exactly 12 entries
    if len(prompts) != 12:
        print(f"Warning: {yaml_file_path} has {len(prompts)} entries after processing, not 12.")
    
    # Update data and write back to file
    data['prompt'] = prompts
    with open(yaml_file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=False)

def main():
    # Directory containing the YAML files
    prompts_dir = "prompts"
    
    # Find all YAML files in the prompts directory
    yaml_files = []
    for file in os.listdir(prompts_dir):
        if file.endswith('.yaml'):
            yaml_files.append(os.path.join(prompts_dir, file))
    
    if not yaml_files:
        print("No YAML files found in prompts directory")
        return
    
    print(f"Found {len(yaml_files)} YAML files to process:")
    for file in yaml_files:
        print(f"  - {file}")
    
    # Process each YAML file
    print("\nProcessing YAML files...")
    for yaml_file in yaml_files:
        try:
            process_yaml_file(yaml_file)
        except Exception as e:
            print(f"Error processing {yaml_file}: {e}")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 