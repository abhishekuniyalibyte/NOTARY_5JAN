import json

# Load all required inputs
with open("customers_index.json", "r", encoding="utf-8") as f:
    customers = json.load(f)

with open("certificate_types.json", "r", encoding="utf-8") as f:
    cert_types = json.load(f)

# Build list of known certificate type keywords
known_keywords = [k for k in cert_types.keys() if k != "otros"]

def matches_type(filename, cert_type):
    """Check if filename contains all parts of the type keyword."""
    name = filename.lower()
    for part in cert_type.split("_"):
        if part not in name:
            return False
    return True

# Prepare output structures
final_certificate_mapping = {k: [] for k in cert_types.keys()}
otros_list = []
non_certificate_docs = []

# Iterate through all customers
for customer, info in customers.items():
    # 1) Certificates
    for cert in info["files"]["certificates"]:
        fname = cert["filename"]
        path = cert["relative_path"]

        matched = False
        best_match = None

        # Try to match to one certificate type
        for ctype in known_keywords:
            if matches_type(fname, ctype):
                matched = True
                best_match = ctype
                break

        if matched:
            final_certificate_mapping[best_match].append({
                "customer": customer,
                "filename": fname,
                "path": path,
                "error_flag": cert["error_flag"]
            })
        else:
            # Goes to OTROS
            final_certificate_mapping["otros"].append({
                "customer": customer,
                "filename": fname,
                "path": path,
                "error_flag": cert["error_flag"]
            })

    # 2) Non certificates
    for doc in info["files"]["non_certificates"]:
        non_certificate_docs.append({
            "customer": customer,
            "filename": doc["filename"],
            "path": doc["relative_path"]
        })

# Build final JSON
summary = {
    "identified_certificate_types": cert_types,
    "certificate_file_mapping": final_certificate_mapping,
    "non_certificate_documents": non_certificate_docs
}

# Save result
with open("certificate_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("certificate_summary.json created successfully!")
