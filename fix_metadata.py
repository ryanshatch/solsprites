"""
Fix script for SolSprites NFT metadata JSON files.
Fixes:
  B) Duplicate/redundant Strain traits
  C) Wrong Type assignments (Sprite -> Mushroom/Cannabis/Plant)
"""

import json
import os

ASSETS_DIR = r"d:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images\candy_machine\assets"

# ---- B: Duplicate Strain fixes ----
# For each file, specify which Strain values to KEEP (remove the rest)
STRAIN_FIXES = {
    102: ["Psilocyben Cubensis"],   # remove redundant "Psilocyben" and "Cubensis"
    121: ["Psilocyben Cubensis"],   # same
    289: ["Pink Kush"],             # remove redundant "Kush"
    322: ["Pink Kush"],             # remove redundant "Kush"
    # 296 has "Borneo" + "Kratom" — these are legitimately two descriptors
    # (Borneo = origin, Kratom = plant type), keeping both
}

# ---- C: Wrong Type fixes ----
TYPE_FIXES = {
    # Should be Mushroom
    92: "Mushroom",
    95: "Mushroom",
    98: "Mushroom",
    113: "Mushroom",
    116: "Mushroom",
    127: "Mushroom",
    291: "Mushroom",
    292: "Mushroom",
    293: "Mushroom",
    294: "Mushroom",
    295: "Mushroom",
    300: "Mushroom",
    301: "Mushroom",
    326: "Mushroom",
    # Should be Cannabis
    258: "Cannabis",
    262: "Cannabis",
    263: "Cannabis",
    264: "Cannabis",
    287: "Cannabis",
    289: "Cannabis",
    299: "Cannabis",
    322: "Cannabis",
    # Should be Plant
    133: "Plant",
    134: "Plant",
    167: "Plant",
    172: "Plant",
    178: "Plant",
    182: "Plant",
    276: "Plant",
    277: "Plant",
    278: "Plant",
    279: "Plant",
    280: "Plant",
    281: "Plant",
    282: "Plant",
    283: "Plant",
    284: "Plant",
}

fixed_count = 0
all_indices = sorted(set(list(STRAIN_FIXES.keys()) + list(TYPE_FIXES.keys())))

for idx in all_indices:
    path = os.path.join(ASSETS_DIR, f"{idx}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    attrs = data.get("attributes", [])

    # Fix B: Remove redundant strains
    if idx in STRAIN_FIXES:
        keep_strains = STRAIN_FIXES[idx]
        new_attrs = []
        for attr in attrs:
            if attr["trait_type"] == "Strain":
                if attr["value"] in keep_strains:
                    new_attrs.append(attr)
                else:
                    print(f"  {idx}.json: Removing redundant Strain='{attr['value']}'")
                    changed = True
            else:
                new_attrs.append(attr)
        attrs = new_attrs

    # Fix C: Correct Type
    if idx in TYPE_FIXES:
        correct_type = TYPE_FIXES[idx]
        for attr in attrs:
            if attr["trait_type"] == "Type":
                if attr["value"] != correct_type:
                    print(f"  {idx}.json: Type '{attr['value']}' -> '{correct_type}'")
                    attr["value"] = correct_type
                    changed = True
                break

    if changed:
        data["attributes"] = attrs
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        fixed_count += 1

print(f"\nFixed {fixed_count} files.")
