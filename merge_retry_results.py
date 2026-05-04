#!/usr/bin/env python3
"""
Merge Condition A retry results into the main eval-results-a.json.

Strategy:
  - Keep original result if it exists AND succeeded (score > 0, no error).
  - Replace with retry result otherwise (missing, failed, or errored).
  - After merge, write merged results back to eval-results-a.json.

Usage:
  python3 merge_retry_results.py
"""
import json
import copy

ORIGINAL = "results/eval-results-a.json"
RETRY    = "results/eval-results-a-retry.json"
OUTPUT   = "results/eval-results-a.json"


def provider_id(r):
    p = r.get("provider")
    return p["id"] if isinstance(p, dict) else str(p)


def scenario_id(r):
    return r.get("vars", {}).get("scenario_id", "")


def is_good(r):
    """Result is usable: not errored and score > 0."""
    return (
        not r.get("error")
        and r.get("score", 0) > 0
    )


def main():
    with open(ORIGINAL) as f:
        orig = json.load(f)
    with open(RETRY) as f:
        retry = json.load(f)

    orig_results = orig["results"]["results"]
    retry_results = retry["results"]["results"]

    # Index original results by (scenario_id, provider_id)
    orig_index = {}
    for r in orig_results:
        key = (scenario_id(r), provider_id(r))
        orig_index[key] = r

    # Index retry results the same way
    retry_index = {}
    for r in retry_results:
        key = (scenario_id(r), provider_id(r))
        retry_index[key] = r

    added = 0
    replaced = 0
    kept = 0

    # Start with original results, replacing bad ones with retry
    merged = []
    for r in orig_results:
        key = (scenario_id(r), provider_id(r))
        if not is_good(r) and key in retry_index and is_good(retry_index[key]):
            merged.append(retry_index[key])
            replaced += 1
        else:
            merged.append(r)
            kept += 1

    # Add retry results that were entirely absent from the original
    for key, r in retry_index.items():
        if key not in orig_index:
            merged.append(r)
            added += 1

    print(f"Original results : {len(orig_results)}")
    print(f"Retry results    : {len(retry_results)}")
    print(f"Kept from orig   : {kept}")
    print(f"Replaced in orig : {replaced}")
    print(f"Added (new)      : {added}")
    print(f"Total merged     : {len(merged)}")

    # Sanity check
    passed = sum(1 for r in merged if r.get("success"))
    failed = sum(1 for r in merged if not r.get("success"))
    errored = sum(1 for r in merged if r.get("error"))
    print(f"  Passed: {passed}  Failed: {failed}  Errored: {errored}")

    # Write merged output
    out = copy.deepcopy(orig)
    out["results"]["results"] = merged
    # Update summary counts
    out["results"]["stats"] = {
        "successes": passed,
        "failures": failed,
        "errors": errored,
        "tokenUsage": {}  # reset; would need to sum if desired
    }

    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nWritten to {OUTPUT}")


if __name__ == "__main__":
    main()
