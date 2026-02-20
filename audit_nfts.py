"""
5-Pass NFT Audit Script
Checks consistency between .json metadata and .png images in candy_machine/assets.
"""

import json
import os
import struct
import zlib
from pathlib import Path
from collections import Counter, defaultdict

ASSETS_DIR = Path(r"d:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images\candy_machine\assets")
SOURCE_IMAGES_DIR = Path(r"d:\00_2026_Files\sol-sprites\solsprites_backup\source_files\assets\images")

# Also check the backup copy
BACKUP_ASSETS_DIR = Path(r"d:\00_2026_Files\sol-sprites\solsprites_backup\backup_assets\candy_machine\assets")

issues = []

def log_issue(pass_num, severity, file_ref, description):
    issues.append({
        "pass": pass_num,
        "severity": severity,
        "file": file_ref,
        "description": description,
    })

def read_png_info(png_path):
    """Read PNG header to get dimensions, bit depth, color type."""
    try:
        with open(png_path, "rb") as f:
            header = f.read(8)
            if header[:8] != b'\x89PNG\r\n\x1a\n':
                return None, "Not a valid PNG file"
            # Read IHDR chunk
            chunk_len = struct.unpack(">I", f.read(4))[0]
            chunk_type = f.read(4)
            if chunk_type != b'IHDR':
                return None, "Missing IHDR chunk"
            ihdr_data = f.read(chunk_len)
            width = struct.unpack(">I", ihdr_data[0:4])[0]
            height = struct.unpack(">I", ihdr_data[4:8])[0]
            bit_depth = ihdr_data[8]
            color_type = ihdr_data[9]
            file_size = os.path.getsize(png_path)
            return {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "file_size": file_size,
            }, None
    except Exception as e:
        return None, str(e)


def pass_1_file_pairing():
    """PASS 1: Verify every N.json has a matching N.png and vice versa."""
    print("=" * 70)
    print("PASS 1: File Pairing — Every N.json must have a matching N.png")
    print("=" * 70)

    json_indices = set()
    png_indices = set()

    for f in ASSETS_DIR.iterdir():
        if f.suffix == ".json" and f.stem.isdigit():
            json_indices.add(int(f.stem))
        elif f.suffix == ".png" and f.stem.isdigit():
            png_indices.add(int(f.stem))

    json_only = sorted(json_indices - png_indices)
    png_only = sorted(png_indices - json_indices)

    if json_only:
        for idx in json_only:
            log_issue(1, "ERROR", f"{idx}.json", f"JSON file exists but {idx}.png is MISSING")
    if png_only:
        for idx in png_only:
            log_issue(1, "ERROR", f"{idx}.png", f"PNG file exists but {idx}.json is MISSING")

    matched = sorted(json_indices & png_indices)

    # Check for gaps in sequence
    if matched:
        expected = list(range(min(matched), max(matched) + 1))
        missing = sorted(set(expected) - set(matched))
        if missing:
            for idx in missing:
                log_issue(1, "ERROR", f"{idx}.json / {idx}.png", f"Gap in sequence — index {idx} is missing both .json and .png")

    found = len(json_only) + len(png_only)
    if found == 0:
        print(f"  [OK] All {len(matched)} indices (0-{max(matched)}) have matching .json and .png files")
    else:
        print(f"  [!!] Found {found} mismatches")

    if not missing if matched else True:
        print(f"  [OK] No gaps in sequence 0-{max(matched) if matched else 'N/A'}")
    else:
        print(f"  [!!] {len(missing)} gaps in sequence: {missing[:20]}{'...' if len(missing) > 20 else ''}")

    return matched


def pass_2_json_internal_consistency(matched_indices):
    """PASS 2: Verify each JSON file's internal references are correct."""
    print()
    print("=" * 70)
    print("PASS 2: JSON Internal Consistency — name, image, uri fields")
    print("=" * 70)

    err_count = 0
    for idx in matched_indices:
        json_path = ASSETS_DIR / f"{idx}.json"
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            log_issue(2, "ERROR", f"{idx}.json", f"Cannot parse JSON: {e}")
            err_count += 1
            continue

        # Check name matches index
        expected_name = f"SolSprites #{idx}"
        actual_name = data.get("name", "")
        if actual_name != expected_name:
            log_issue(2, "ERROR", f"{idx}.json", f"Name mismatch: expected '{expected_name}', got '{actual_name}'")
            err_count += 1

        # Check image field
        expected_image = f"{idx}.png"
        actual_image = data.get("image", "")
        if actual_image != expected_image:
            log_issue(2, "ERROR", f"{idx}.json", f"Image field mismatch: expected '{expected_image}', got '{actual_image}'")
            err_count += 1

        # Check properties.files[0].uri
        files = data.get("properties", {}).get("files", [])
        if not files:
            log_issue(2, "ERROR", f"{idx}.json", "Missing properties.files array")
            err_count += 1
        else:
            uri = files[0].get("uri", "")
            if uri != expected_image:
                log_issue(2, "ERROR", f"{idx}.json", f"File URI mismatch: expected '{expected_image}', got '{uri}'")
                err_count += 1
            ftype = files[0].get("type", "")
            if ftype != "image/png":
                log_issue(2, "WARN", f"{idx}.json", f"File type is '{ftype}' instead of 'image/png'")
                err_count += 1

        # Check symbol
        if data.get("symbol") != "SPRITE":
            log_issue(2, "WARN", f"{idx}.json", f"Symbol is '{data.get('symbol')}' (expected 'SPRITE')")
            err_count += 1

        # Check seller_fee_basis_points
        if data.get("seller_fee_basis_points") != 1000:
            log_issue(2, "WARN", f"{idx}.json", f"seller_fee_basis_points is {data.get('seller_fee_basis_points')} (expected 1000)")
            err_count += 1

        # Check creators
        creators = data.get("properties", {}).get("creators", [])
        if not creators:
            log_issue(2, "ERROR", f"{idx}.json", "Missing creators")
            err_count += 1
        elif creators[0].get("address") != "777ePKXhcxMdJPMA22YeiR6pdMUTadnpT7AUyto2Y24N":
            log_issue(2, "ERROR", f"{idx}.json", f"Creator address wrong: {creators[0].get('address')}")
            err_count += 1
        elif creators[0].get("share") != 100:
            log_issue(2, "WARN", f"{idx}.json", f"Creator share is {creators[0].get('share')} (expected 100)")
            err_count += 1

    if err_count == 0:
        print(f"  [OK] All {len(matched_indices)} JSON files have correct internal references")
    else:
        print(f"  [!!] Found {err_count} issues in internal consistency")


def pass_3_attribute_validity(matched_indices):
    """PASS 3: Validate attribute schema and value validity."""
    print()
    print("=" * 70)
    print("PASS 3: Attribute Validity — required traits, valid values, schema")
    print("=" * 70)

    VALID_ELEMENTS = {"Air", "Earth", "Electric", "Fire", "Light", "Magic", "Shadow", "Water", "Unknown", "Forest", "Fern", "Sunflower", "Spleenwort", "Calypso", "Void"}
    VALID_TYPES = {"Cannabis", "Cubes", "Mushroom", "Plant", "Root", "Sprite", "Goblin", "Fairy"}
    REQUIRED_TRAITS = {"Element", "Type", "Background"}
    KNOWN_TRAIT_TYPES = {"Element", "Type", "Strain", "Background", "Sprite Color", "Aura", "Aura Style", "Motif", "Accessory", "Variant"}

    err_count = 0
    warn_count = 0
    missing_element = []
    missing_type = []
    missing_bg = []
    unknown_traits = defaultdict(list)
    empty_values = []
    duplicate_traits = []

    for idx in matched_indices:
        json_path = ASSETS_DIR / f"{idx}.json"
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            continue

        attrs = data.get("attributes", [])
        if not attrs:
            log_issue(3, "ERROR", f"{idx}.json", "No attributes at all")
            err_count += 1
            continue

        trait_types_seen = []
        for attr in attrs:
            tt = attr.get("trait_type", "")
            vv = attr.get("value", "")

            if not tt:
                log_issue(3, "ERROR", f"{idx}.json", f"Attribute with empty trait_type: {attr}")
                err_count += 1
                continue

            if not vv:
                log_issue(3, "WARN", f"{idx}.json", f"Attribute '{tt}' has empty value")
                warn_count += 1
                empty_values.append(idx)

            trait_types_seen.append(tt)

            if tt not in KNOWN_TRAIT_TYPES:
                log_issue(3, "WARN", f"{idx}.json", f"Unknown trait_type: '{tt}'")
                unknown_traits[tt].append(idx)
                warn_count += 1

            # Validate Element values
            if tt == "Element" and vv not in VALID_ELEMENTS:
                log_issue(3, "WARN", f"{idx}.json", f"Unusual Element value: '{vv}'")
                warn_count += 1

            # Validate Type values
            if tt == "Type" and vv not in VALID_TYPES:
                log_issue(3, "WARN", f"{idx}.json", f"Unusual Type value: '{vv}'")
                warn_count += 1

        # Check for required traits
        for req in REQUIRED_TRAITS:
            if req not in trait_types_seen:
                log_issue(3, "ERROR", f"{idx}.json", f"Missing required trait: {req}")
                err_count += 1
                if req == "Element": missing_element.append(idx)
                elif req == "Type": missing_type.append(idx)
                elif req == "Background": missing_bg.append(idx)

        # Check for duplicate trait types (same trait_type appearing more than once)
        trait_counter = Counter(trait_types_seen)
        for tt, count in trait_counter.items():
            if count > 1:
                log_issue(3, "WARN", f"{idx}.json", f"Duplicate trait_type '{tt}' appears {count} times")
                warn_count += 1
                duplicate_traits.append((idx, tt, count))

    if err_count == 0 and warn_count == 0:
        print(f"  [OK] All {len(matched_indices)} JSON files have valid attributes")
    else:
        print(f"  [!!] {err_count} errors, {warn_count} warnings in attribute validation")
        if missing_element:
            print(f"       Missing Element: indices {missing_element[:20]}")
        if missing_type:
            print(f"       Missing Type: indices {missing_type[:20]}")
        if missing_bg:
            print(f"       Missing Background: indices {missing_bg[:20]}")
        if duplicate_traits:
            print(f"       Duplicate traits: {duplicate_traits[:20]}")


def pass_4_png_validity(matched_indices):
    """PASS 4: Verify PNG files are valid images with consistent dimensions."""
    print()
    print("=" * 70)
    print("PASS 4: PNG Validity — file integrity, dimensions, consistency")
    print("=" * 70)

    infos = {}
    err_count = 0
    dimensions = Counter()

    for idx in matched_indices:
        png_path = ASSETS_DIR / f"{idx}.png"
        info, error = read_png_info(png_path)
        if error:
            log_issue(4, "ERROR", f"{idx}.png", f"Invalid PNG: {error}")
            err_count += 1
            continue

        infos[idx] = info
        dim_key = f"{info['width']}x{info['height']}"
        dimensions[dim_key] += 1

        # Check for suspiciously small files (< 1KB likely corrupted)
        if info["file_size"] < 100:
            log_issue(4, "ERROR", f"{idx}.png", f"Suspiciously small file: {info['file_size']} bytes")
            err_count += 1

        # Check for zero-dimension images
        if info["width"] == 0 or info["height"] == 0:
            log_issue(4, "ERROR", f"{idx}.png", f"Zero dimensions: {info['width']}x{info['height']}")
            err_count += 1

    # Check dimension consistency
    if len(dimensions) > 1:
        most_common_dim = dimensions.most_common(1)[0][0]
        log_issue(4, "WARN", "collection", f"Mixed dimensions detected: {dict(dimensions)}")
        for idx, info in infos.items():
            dim = f"{info['width']}x{info['height']}"
            if dim != most_common_dim:
                log_issue(4, "WARN", f"{idx}.png", f"Non-standard dimension: {dim} (majority is {most_common_dim})")
        print(f"  [!!] Mixed dimensions: {dict(dimensions)}")
    else:
        dim = list(dimensions.keys())[0] if dimensions else "N/A"
        print(f"  [OK] All {len(infos)} PNGs have consistent dimensions: {dim}")

    # File size statistics
    if infos:
        sizes = [v["file_size"] for v in infos.values()]
        avg_size = sum(sizes) / len(sizes)
        min_size = min(sizes)
        max_size = max(sizes)
        min_idx = min(infos, key=lambda k: infos[k]["file_size"])
        max_idx = max(infos, key=lambda k: infos[k]["file_size"])

        print(f"  File sizes: min={min_size:,}B ({min_idx}.png), max={max_size:,}B ({max_idx}.png), avg={avg_size:,.0f}B")

        # Flag outliers (files < 10% or > 500% of average)
        for idx, info in infos.items():
            if info["file_size"] < avg_size * 0.05:
                log_issue(4, "WARN", f"{idx}.png", f"Unusually small: {info['file_size']:,}B (avg {avg_size:,.0f}B)")
            elif info["file_size"] > avg_size * 10:
                log_issue(4, "WARN", f"{idx}.png", f"Unusually large: {info['file_size']:,}B (avg {avg_size:,.0f}B)")

    if err_count == 0:
        print(f"  [OK] All {len(matched_indices)} PNGs are valid")
    else:
        print(f"  [!!] {err_count} PNG validity errors")


def pass_5_cross_reference(matched_indices):
    """PASS 5: Cross-reference source PNGs to output, check backup consistency."""
    print()
    print("=" * 70)
    print("PASS 5: Cross-Reference — source images, backup consistency, trait audit")
    print("=" * 70)

    err_count = 0

    # 5a: Check if source images exist and load index_map if available
    index_map_path = ASSETS_DIR / "index_map.json"
    if index_map_path.exists():
        with open(index_map_path, "r", encoding="utf-8") as f:
            index_map = json.load(f)
        print(f"  Index map loaded: {len(index_map)} entries")

        # Check each entry in index_map
        for entry in index_map:
            final_idx = entry.get("final_idx")
            src_file = entry.get("src_file", "")
            src_path = SOURCE_IMAGES_DIR / src_file
            if not src_path.exists():
                log_issue(5, "WARN", f"{final_idx}.png", f"Source file missing: {src_file}")
    else:
        print("  [SKIP] No index_map.json found")

    # 5b: Compare main assets to backup assets
    if BACKUP_ASSETS_DIR.exists():
        backup_jsons = {f.name for f in BACKUP_ASSETS_DIR.iterdir() if f.suffix == ".json" and f.stem.isdigit()}
        main_jsons = {f.name for f in ASSETS_DIR.iterdir() if f.suffix == ".json" and f.stem.isdigit()}

        only_main = sorted(main_jsons - backup_jsons)
        only_backup = sorted(backup_jsons - main_jsons)

        if only_main:
            print(f"  [INFO] JSONs only in main (not in backup): {only_main[:20]}")
        if only_backup:
            print(f"  [INFO] JSONs only in backup (not in main): {only_backup[:20]}")

        # Compare JSON content between main and backup
        shared = main_jsons & backup_jsons
        diff_count = 0
        for name in sorted(shared):
            main_path = ASSETS_DIR / name
            backup_path = BACKUP_ASSETS_DIR / name
            try:
                with open(main_path, "r", encoding="utf-8") as f:
                    main_data = json.load(f)
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)

                # Compare attributes specifically
                main_attrs = {(a["trait_type"], a["value"]) for a in main_data.get("attributes", [])}
                backup_attrs = {(a["trait_type"], a["value"]) for a in backup_data.get("attributes", [])}

                if main_attrs != backup_attrs:
                    added = main_attrs - backup_attrs
                    removed = backup_attrs - main_attrs
                    idx = name.replace(".json", "")
                    details = []
                    if added:
                        details.append(f"added: {added}")
                    if removed:
                        details.append(f"removed: {removed}")
                    log_issue(5, "INFO", f"{idx}.json", f"Differs from backup: {'; '.join(details)}")
                    diff_count += 1
            except Exception as e:
                pass

        if diff_count == 0:
            print(f"  [OK] All {len(shared)} shared JSONs match between main and backup")
        else:
            print(f"  [!!] {diff_count} JSONs differ between main and backup")

        # Compare PNG sizes between main and backup
        backup_pngs = {f.name for f in BACKUP_ASSETS_DIR.iterdir() if f.suffix == ".png" and f.stem.isdigit()}
        main_pngs = {f.name for f in ASSETS_DIR.iterdir() if f.suffix == ".png" and f.stem.isdigit()}
        shared_pngs = main_pngs & backup_pngs
        png_diff_count = 0
        for name in sorted(shared_pngs):
            main_size = os.path.getsize(ASSETS_DIR / name)
            backup_size = os.path.getsize(BACKUP_ASSETS_DIR / name)
            if main_size != backup_size:
                idx = name.replace(".png", "")
                log_issue(5, "WARN", f"{idx}.png", f"PNG differs from backup: main={main_size:,}B backup={backup_size:,}B")
                png_diff_count += 1

        if png_diff_count == 0:
            print(f"  [OK] All {len(shared_pngs)} shared PNGs match (size) between main and backup")
        else:
            print(f"  [!!] {png_diff_count} PNGs differ in size between main and backup")
    else:
        print("  [SKIP] No backup directory found")

    # 5c: Validate trait_audit.json matches actual data
    audit_path = ASSETS_DIR / "_trait_audit.json"
    if audit_path.exists():
        with open(audit_path, "r", encoding="utf-8") as f:
            audit = json.load(f)

        audit_count = audit.get("items_written", 0)
        if audit_count != len(matched_indices):
            log_issue(5, "ERROR", "_trait_audit.json", f"items_written={audit_count} but found {len(matched_indices)} actual items")
            err_count += 1
        else:
            print(f"  [OK] Trait audit items_written ({audit_count}) matches actual count")

        # Recount traits from actual JSONs and compare to audit
        actual_trait_counts = Counter()
        actual_values_by_trait = defaultdict(set)

        for idx in matched_indices:
            json_path = ASSETS_DIR / f"{idx}.json"
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for attr in data.get("attributes", []):
                    tt = attr.get("trait_type", "")
                    vv = attr.get("value", "")
                    actual_trait_counts[tt] += 1
                    if vv:
                        actual_values_by_trait[tt].add(vv)
            except:
                pass

        # Compare counts
        audit_trait_counts = audit.get("trait_types_seen", {})
        for tt in set(list(actual_trait_counts.keys()) + list(audit_trait_counts.keys())):
            actual = actual_trait_counts.get(tt, 0)
            audited = audit_trait_counts.get(tt, 0)
            if actual != audited:
                log_issue(5, "WARN", "_trait_audit.json",
                          f"Trait count mismatch for '{tt}': audit says {audited}, actual JSON files have {actual}")

        # Compare unique values
        audit_values = audit.get("unique_values_by_trait", {})
        for tt in set(list(actual_values_by_trait.keys()) + list(audit_values.keys())):
            actual_vals = actual_values_by_trait.get(tt, set())
            audit_vals = set(audit_values.get(tt, []))
            only_actual = actual_vals - audit_vals
            only_audit = audit_vals - actual_vals
            if only_actual:
                log_issue(5, "WARN", "_trait_audit.json",
                          f"Values in JSONs but not in audit for '{tt}': {only_actual}")
            if only_audit:
                log_issue(5, "WARN", "_trait_audit.json",
                          f"Values in audit but not in JSONs for '{tt}': {only_audit}")
    else:
        print("  [SKIP] No _trait_audit.json found")


def print_summary():
    print()
    print("=" * 70)
    print("SUMMARY OF ALL ISSUES")
    print("=" * 70)

    if not issues:
        print("  NO ISSUES FOUND — Collection looks clean!")
        return

    errors = [i for i in issues if i["severity"] == "ERROR"]
    warnings = [i for i in issues if i["severity"] == "WARN"]
    infos = [i for i in issues if i["severity"] == "INFO"]

    print(f"  Total: {len(issues)} issues ({len(errors)} ERRORS, {len(warnings)} WARNINGS, {len(infos)} INFO)")
    print()

    if errors:
        print("  --- ERRORS (must fix) ---")
        for i in errors:
            print(f"    [Pass {i['pass']}] {i['file']}: {i['description']}")

    if warnings:
        print()
        print("  --- WARNINGS (review recommended) ---")
        for i in warnings:
            print(f"    [Pass {i['pass']}] {i['file']}: {i['description']}")

    if infos:
        print()
        print("  --- INFO (differences from backup, may be intentional) ---")
        for i in infos[:50]:
            print(f"    [Pass {i['pass']}] {i['file']}: {i['description']}")
        if len(infos) > 50:
            print(f"    ... and {len(infos) - 50} more INFO items")


if __name__ == "__main__":
    print("NFT Collection Audit — 5 Passes")
    print(f"Assets dir: {ASSETS_DIR}")
    print(f"Source dir: {SOURCE_IMAGES_DIR}")
    print()

    matched = pass_1_file_pairing()
    pass_2_json_internal_consistency(matched)
    pass_3_attribute_validity(matched)
    pass_4_png_validity(matched)
    pass_5_cross_reference(matched)
    print_summary()
