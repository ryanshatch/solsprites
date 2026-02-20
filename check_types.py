import json, os
base = r'd:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images\candy_machine\assets'
src = r'd:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images'

for idx in [127, 133, 134, 167, 289, 296, 322]:
    p = os.path.join(base, f'{idx}.json')
    d = json.load(open(p))
    attrs = [(a['trait_type'], a['value']) for a in d['attributes']]
    print(f"{idx}.json => {attrs}")

    # Find source PNG name
    for f in os.listdir(src):
        if f.startswith(f"{idx}_") and f.endswith(".png"):
            print(f"  source: {f}")
            break
    else:
        # Check subdirs
        for root, dirs, files in os.walk(src):
            for f in files:
                if f.startswith(f"{idx}_") and f.endswith(".png"):
                    print(f"  source: {os.path.relpath(os.path.join(root, f), src)}")
                    break
