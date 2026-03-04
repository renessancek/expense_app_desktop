import time
import os
import tempfile
import json
from categorizer import Categorizer

def create_dummy_rules(num_rules, num_mappings):
    rules = []
    for i in range(num_rules):
        rules.append({
            "keywords": [f"keyword_{i}_a", f"keyword_{i}_b"],
            "category": f"category_rule_{i}"
        })

    mappings = {}
    for i in range(num_mappings):
        mappings[f"mapping_keyword_{i}"] = f"category_mapping_{i}"

    return {"rules": rules, "mappings": mappings}

def run_benchmark():
    # Create a temporary rules file
    fd, path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(create_dummy_rules(100, 1000), f)

        categorizer = Categorizer(rules_path=path)

        # Test dataset
        descriptions = [
            "This is a random description mapping_keyword_500 that should match.",
            "Another keyword_50_a test that matches rules.",
            "Something completely different that won't match anything at all.",
            "mapping_keyword_999 is at the beginning.",
            "End of the string mapping_keyword_10",
        ] * 200 # 1000 descriptions total

        start_time = time.perf_counter()

        matched = 0
        unmatched = 0

        for desc in descriptions:
            cat = categorizer.suggest_category(desc)
            if cat != 'Sonstiges':
                matched += 1
            else:
                unmatched += 1

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        print(f"Benchmark completed in {elapsed:.4f} seconds.")
        print(f"Processed {len(descriptions)} descriptions.")
        print(f"Matched: {matched}, Unmatched: {unmatched}")
        return elapsed

    finally:
        os.remove(path)

if __name__ == "__main__":
    run_benchmark()
