"""
Quick test to verify the fixes work
"""
import json
import os
import unicodedata

def normalize_path(path):
    """Normalize Unicode path to NFC form for consistent filesystem access"""
    return unicodedata.normalize('NFC', path)

def find_file_case_insensitive(base_path, customer, relative_path):
    """
    Try to find file with Unicode normalization and case-insensitive matching.
    Returns the actual file path if found, None otherwise.
    """
    # Normalize all paths
    customer_folder = os.path.join(base_path, normalize_path(customer))

    # First try direct match with NFC normalization
    direct_path = os.path.join(customer_folder, normalize_path(relative_path))
    if os.path.exists(direct_path):
        return direct_path

    # If direct match fails, try to find it in the directory
    if os.path.exists(customer_folder):
        try:
            actual_files = os.listdir(customer_folder)
            normalized_target = normalize_path(relative_path).lower()

            for actual_file in actual_files:
                if normalize_path(actual_file).lower() == normalized_target:
                    return os.path.join(customer_folder, actual_file)
        except Exception:
            pass

    return None

# Test the Unicode normalization fix
print("=" * 70)
print("TESTING UNICODE PATH RESOLUTION FIX")
print("=" * 70)

with open("customers_index.json", "r", encoding="utf-8") as f:
    customers = json.load(f)

base_path = "Notaria"
customer = "Amura Advisors Ltda"

# Get the problematic ABITAB files
abitab_files = [c for c in customers[customer]['files']['certificates']
                if 'ABITAB' in c['filename'] and 'Albanell' in c['filename']]

print(f"\nTesting {len(abitab_files)} ABITAB files:")
print("-" * 70)

found_count = 0
not_found_count = 0

for cert in abitab_files:
    filename = cert['filename']
    old_path = os.path.join(base_path, customer, cert["relative_path"])
    new_path = find_file_case_insensitive(base_path, customer, cert["relative_path"])

    old_exists = os.path.exists(old_path)
    new_exists = new_path is not None

    print(f"\nFile: {filename[:60]}...")
    print(f"  Old method (direct join): {'✓ FOUND' if old_exists else '✗ NOT FOUND'}")
    print(f"  New method (normalized):  {'✓ FOUND' if new_exists else '✗ NOT FOUND'}")

    if new_exists:
        found_count += 1
    else:
        not_found_count += 1

print("\n" + "=" * 70)
print(f"RESULTS: {found_count} found, {not_found_count} not found")
print("=" * 70)

if found_count == len(abitab_files):
    print("✓ SUCCESS! All ABITAB files can now be found!")
else:
    print("✗ FAILED: Some files still not found")
