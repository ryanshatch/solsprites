"""Deep type-mismatch check: find all items where Strain suggests a different Type."""
import json, os

base = r'd:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images\candy_machine\assets'
src = r'd:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images'

CANNABIS_STRAINS = {
    "Pink Kush", "Kush", "Indica", "Sativa", "Gorilla Glue",
    "Girl Scout Cookies", "Death Star", "Green Md", "White Md"
}
MUSHROOM_STRAINS = {
    "Golden Teacher", "Psilocyben Cubensis", "Sacred Mexica", "Wavy Caps",
    "Shaggy Mane", "Liberty Cap", "Teonanacatl", "Agaric", "Bohemica",
    "Cyanscens", "Cubensis", "Psilocyben", "Psilocybin", "Reshi",
    "Flying Saucer", "Z Strain", "Knobby Tops", "Philosophers Stone",
    "Shaggy Mane", "Inky Cap", "Ink"
}
PLANT_STRAINS = {
    "Khat Plant", "Cocoa Plant", "Poppy Plant", "Willow Tree",
    "San Pedro", "Kratom", "Borneo", "Dmt", "Ayahuasca Plant"
}

type_issues = []
for idx in range(333):
    p = os.path.join(base, f'{idx}.json')
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    attrs = d.get('attributes', [])
    
    type_val = None
    strains = []
    for a in attrs:
        if a['trait_type'] == 'Type':
            type_val = a['value']
        if a['trait_type'] == 'Strain':
            strains.append(a['value'])
    
    for strain in strains:
        expected_type = None
        if strain in CANNABIS_STRAINS:
            expected_type = "Cannabis"
        elif strain in MUSHROOM_STRAINS:
            expected_type = "Mushroom"
        elif strain in PLANT_STRAINS:
            expected_type = "Plant"
        
        if expected_type and type_val != expected_type:
            # Find source filename
            src_name = "?"
            for f in os.listdir(src):
                if f.startswith(f"{idx}_") and f.endswith(".png"):
                    src_name = f
                    break
            type_issues.append((idx, type_val, expected_type, strain, src_name))

if type_issues:
    print(f"Found {len(type_issues)} potential Type mismatches:")
    for idx, actual, expected, strain, src_name in type_issues:
        print(f"  {idx}.json / {idx}.png: Type='{actual}' but Strain='{strain}' suggests Type='{expected}'")
        print(f"    source: {src_name}")
else:
    print("No Type/Strain mismatches found.")

# Also check for duplicate strains
print("\nDuplicate Strain check:")
for idx in range(333):
    p = os.path.join(base, f'{idx}.json')
    if not os.path.exists(p):
        continue
    d = json.load(open(p))
    strains = [a['value'] for a in d.get('attributes', []) if a['trait_type'] == 'Strain']
    if len(strains) > 1:
        # Check if any strain is a substring/component of another
        compound = None
        parts = []
        for s in strains:
            if ' ' in s:
                compound = s
            else:
                parts.append(s)
        if compound and parts:
            compound_words = set(compound.lower().split())
            part_words = set(p.lower() for p in parts)
            if part_words.issubset(compound_words):
                print(f"  {idx}.json: REDUNDANT strains {strains} — '{compound}' already contains {parts}")
            else:
                print(f"  {idx}.json: Multiple strains {strains}")
        else:
            print(f"  {idx}.json: Multiple strains {strains}")
