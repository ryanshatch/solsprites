import json, os
from collections import Counter, defaultdict

base = r"d:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images\candy_machine\assets"
audit_path = os.path.join(base, "_trait_audit.json")

trait_counts = Counter()
values_by_trait = defaultdict(set)

for idx in range(333):
    p = os.path.join(base, f"{idx}.json")
    d = json.load(open(p))
    for a in d.get("attributes", []):
        tt = a["trait_type"]
        vv = a["value"]
        trait_counts[tt] += 1
        if vv:
            values_by_trait[tt].add(vv)

with open(audit_path, "r") as f:
    audit = json.load(f)

audit["trait_types_seen"] = dict(trait_counts)
audit["unique_values_by_trait"] = {k: sorted(list(v)) for k, v in values_by_trait.items()}

with open(audit_path, "w") as f:
    json.dump(audit, f, indent=2)

print("Updated _trait_audit.json")
for k, v in sorted(trait_counts.items()):
    print(f"  {k}: {v}")
print("Type values:", sorted(values_by_trait["Type"]))
