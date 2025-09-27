import os
import re
import ast
from manual_matching_dictionary import manual_matching_dictionary

def find_potential_match_files():
    """Finds all potential match files in the current directory."""
    return [f for f in os.listdir('.') if re.match(r'potential_matches_\d+_\d+\.txt', f)]

def parse_potential_matches(file_path):
    """Parses a potential matches file and returns a dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        # Using ast.literal_eval for safe evaluation of the string as a Python literal
        return ast.literal_eval(content)
    except (ValueError, SyntaxError) as e:
        print(f"Could not parse {file_path}: {e}")
        return {}

def main():
    """Main function to merge dictionaries."""
    combined_matches = manual_matching_dictionary.copy()

    match_files = find_potential_match_files()
    if not match_files:
        print("No potential match files found.")
        return

    print(f"Found files to merge: {match_files}")

    for file in match_files:
        print(f"Processing {file}...")
        new_matches = parse_potential_matches(file)
        combined_matches.update(new_matches)
        print(f"Merged {len(new_matches)} new entries.")

    # Write the updated dictionary back to the file
    with open('manual_matching_dictionary.py', 'w', encoding='utf-8') as f:
        f.write("manual_matching_dictionary = {\n")
        for key, value in sorted(combined_matches.items()):
            key_escaped = key.replace('"', '\\"')
            value_escaped = value.replace('"', '\\"')
            f.write(f'    "{key_escaped}": "{value_escaped}",\n')
        f.write("}\n")

    print(f"\nSuccessfully updated manual_matching_dictionary.py with a total of {len(combined_matches)} entries.")

if __name__ == "__main__":
    main()