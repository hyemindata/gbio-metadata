#!/usr/bin/env python3
import yaml
import os

def clear_yaml_file(yaml_file_path):
    """
    Clear the contents of a YAML file
    """
    with open(yaml_file_path, 'w') as f:
        f.truncate(0)
    print(f"Cleared: {yaml_file_path}")

def main():
    # Files to be cleared
    files_to_clear = [
        "prompts/biomes4_E_selects.yaml",
        "prompts/biomes4_F_selects.yaml",
        "prompts/biomes4_G_selects.yaml",
        "prompts/biomes4_H_selects.yaml"
    ]
    
    print("Clearing specified YAML files...")
    for file in files_to_clear:
        try:
            if os.path.exists(file):
                clear_yaml_file(file)
            else:
                print(f"File not found: {file}")
        except Exception as e:
            print(f"Error clearing {file}: {e}")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 