#!/usr/bin/env python3
import json
import yaml
import os
import shutil
from pathlib import Path

def extract_text_to_yaml(json_file_path):
    """
    Extract 'text' field from JSON file and save as YAML with 'prompt' key
    """
    # Read JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Extract text from each entry
    prompts = []
    for key in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else x):
        if 'text' in data[key]:
            prompts.append(data[key]['text'])
    
    # Create YAML structure
    yaml_data = {'prompt': prompts}
    
    # Create output filename (replace .json with .yaml)
    output_path = json_file_path.replace('.json', '.yaml')
    
    # Write YAML file
    with open(output_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created: {output_path}")
    return output_path

def move_original_files(json_files, backup_dir):
    """
    Move original JSON files to backup directory
    """
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    for json_file in json_files:
        filename = os.path.basename(json_file)
        backup_path = os.path.join(backup_dir, filename)
        shutil.move(json_file, backup_path)
        print(f"Moved: {json_file} -> {backup_path}")

def main():
    # Directory containing the JSON files
    prompts_dir = "prompts"
    
    # Find all JSON files in the prompts directory
    json_files = []
    for file in os.listdir(prompts_dir):
        if file.endswith('.json'):
            json_files.append(os.path.join(prompts_dir, file))
    
    if not json_files:
        print("No JSON files found in prompts directory")
        return
    
    print(f"Found {len(json_files)} JSON files:")
    for file in json_files:
        print(f"  - {file}")
    
    # Extract text to YAML for each file
    print("\nExtracting text to YAML...")
    for json_file in json_files:
        try:
            extract_text_to_yaml(json_file)
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Move original files to backup
    backup_dir = "prompts_backup"
    print(f"\nMoving original files to {backup_dir}...")
    move_original_files(json_files, backup_dir)
    
    print("\nDone!")

if __name__ == "__main__":
    main() 