"""Remove 'dummy' references from all collections in MongoDB.

Cleans up any test/dummy markers from cache labels and other fields.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from argus_agent.src.db.mongo import get_fortyguard_cache_collection, get_anomalies_collection


def cleanup_cache() -> int:
    """Remove 'dummy' from fortyguard_cache labels."""
    cache = get_fortyguard_cache_collection()

    # Find all docs with 'dummy' in label
    docs_with_dummy = list(cache.find({"label": {"$regex": "dummy"}}))

    if not docs_with_dummy:
        print("✓ No 'dummy' labels in fortyguard_cache")
        return 0

    print(f"Found {len(docs_with_dummy)} cache entries with 'dummy' in label")

    updated = 0
    for doc in docs_with_dummy:
        new_label = doc["label"].replace(" (dummy)", "").replace(" dummy", "")
        cache.update_one(
            {"_id": doc["_id"]},
            {"$set": {"label": new_label}}
        )
        updated += 1
        print(f"  Updated: {new_label}")

    return updated


def cleanup_anomalies() -> int:
    """Remove 'dummy' markers from anomalies if any."""
    anom = get_anomalies_collection()

    # Check for any dummy markers (unlikely, but be thorough)
    docs_with_dummy = list(anom.find({"stage": {"$regex": "dummy"}}))

    if not docs_with_dummy:
        print("✓ No 'dummy' markers in anomalies")
        return 0

    print(f"Found {len(docs_with_dummy)} anomalies with 'dummy' markers")
    updated = 0
    for doc in docs_with_dummy:
        new_stage = doc["stage"].replace(" (dummy)", "").replace(" dummy", "")
        anom.update_one(
            {"_id": doc["_id"]},
            {"$set": {"stage": new_stage}}
        )
        updated += 1

    return updated


def main() -> None:
    """Clean up all dummy references in MongoDB."""
    print("Cleaning up 'dummy' references from MongoDB…\n")

    cache_updated = cleanup_cache()
    anom_updated = cleanup_anomalies()

    total = cache_updated + anom_updated

    if total == 0:
        print("\n✓ No dummy references found — data is clean")
    else:
        print(f"\n✓ Cleaned up {total} documents")

    # Verify
    cache = get_fortyguard_cache_collection()
    anom = get_anomalies_collection()

    dummy_cache = cache.count_documents({"label": {"$regex": "dummy"}})
    dummy_anom = anom.count_documents({"stage": {"$regex": "dummy"}})

    if dummy_cache == 0 and dummy_anom == 0:
        print("✓ Verification: No 'dummy' references remain")
    else:
        print(f"⚠ Verification failed: {dummy_cache} cache, {dummy_anom} anomalies still have dummy refs")


if __name__ == "__main__":
    main()
