#!/usr/bin/env python3
import yaml
import os
import re
import unicodedata

def clean_text(text):
    """
    Clean text by removing escape sequences and converting Unicode to ASCII
    """
    # Remove backslash escapes
    text = text.replace('\\', '')
    
    # Convert common Unicode characters to ASCII equivalents
    unicode_mappings = {
        '\u2014': '--',  # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quotation mark
        '\u2019': "'",   # right single quotation mark
        '\u201c': '"',   # left double quotation mark
        '\u201d': '"',   # right double quotation mark
        '\u2026': '...', # horizontal ellipsis
        '\u00a0': ' ',   # non-breaking space
    }
    
    for unicode_char, ascii_char in unicode_mappings.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Normalize Unicode characters to closest ASCII equivalent
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Remove any remaining non-ASCII characters (optional, uncomment if needed)
    # text = text.encode('ascii', 'ignore').decode('ascii')
    
    return text

def clean_yaml_file(yaml_file_path):
    """
    Clean a YAML file by processing all text fields
    """
    # Read YAML file
    with open(yaml_file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Clean prompts if they exist
    if 'prompt' in data and isinstance(data['prompt'], list):
        cleaned_prompts = []
        for prompt in data['prompt']:
            cleaned_prompt = clean_text(prompt)
            cleaned_prompts.append(cleaned_prompt)
        data['prompt'] = cleaned_prompts
    
    # Write cleaned YAML file
    with open(yaml_file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=False)
    
    print(f"Cleaned: {yaml_file_path}")

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
    
    print(f"Found {len(yaml_files)} YAML files to clean:")
    for file in yaml_files:
        print(f"  - {file}")
    
    # Clean each YAML file
    print("\nCleaning YAML files...")
    for yaml_file in yaml_files:
        try:
            clean_yaml_file(yaml_file)
        except Exception as e:
            print(f"Error cleaning {yaml_file}: {e}")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 