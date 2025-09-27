import re
import sys
from thefuzz import process

def parse_debug_report(file_path='debug_report.txt'):
    """Parses the debug report to extract unmatched and unused items."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        unmatched_section = content.split('СЕКЦИЯ 1: ТОВАРЫ БЕЗ СОВПАДЕНИЙ')[1].split('СЕКЦИЯ 2: НЕИСПОЛЬЗОВАННЫЕ ТОВАРЫ ИЗ КАТАЛОГОВ')[0]
        unused_section = content.split('СЕКЦИЯ 2: НЕИСПОЛЬЗОВАННЫЕ ТОВАРЫ ИЗ КАТАЛОГОВ')[1]
    except IndexError:
        print("Could not find the expected sections in the debug report.")
        return [], []

    unmatched_items = [line.split(':', 1)[1].strip() for line in unmatched_section.strip().split('\n') if line.startswith('Строка')]
    unused_items = [line.strip() for line in unused_section.strip().split('\n') if line.strip()]

    return unmatched_items, unused_items

def generate_potential_matches(unmatched_items, unused_items, score_cutoff=80):
    """Generates potential matches using fuzzy string matching."""
    potential_matches = {}
    total_items = len(unmatched_items)
    print(f"Processing {total_items} items in this batch...")

    for i, item in enumerate(unmatched_items):
        if (i + 1) % 50 == 0:
            print(f"  ...processed {i + 1}/{total_items}")

        match = process.extractOne(item, unused_items, score_cutoff=score_cutoff)
        if match:
            potential_matches[item] = match[0]

    return potential_matches

def main():
    """Main function to run the dictionary generation process."""
    if len(sys.argv) != 3:
        print("Usage: python generate_dictionary.py <start_index> <end_index>")
        return

    start_index = int(sys.argv[1])
    end_index = int(sys.argv[2])

    unmatched_all, unused = parse_debug_report()
    if not unmatched_all or not unused:
        print("No items to process. Exiting.")
        return

    # Select the batch of items to process
    unmatched_batch = unmatched_all[start_index:end_index]

    potential_matches = generate_potential_matches(unmatched_batch, unused)

    output_filename = f'potential_matches_{start_index}_{end_index}.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("{\n")
        for excel_name, catalog_name in potential_matches.items():
            excel_name_escaped = excel_name.replace('"', '\\"')
            catalog_name_escaped = catalog_name.replace('"', '\\"')
            f.write(f'    "{excel_name_escaped}": "{catalog_name_escaped}",\n')
        f.write("}\n")

    print(f"Generated {output_filename} with {len(potential_matches)} potential matches.")

if __name__ == "__main__":
    main()