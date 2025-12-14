
import os
import sys
import django
from pprint import pprint

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from movies.search import search_shows

def test_query(query):
    print(f"\n--- Testing Query: '{query}' ---")
    try:
        results, structured = search_shows(query, top_k=3)
        print("Parsed Structured Output:")
        pprint(structured)
        print(f"Found {len(results)} results.")
        for r in results:
            # We can't easily see the weighted distance unless we inspect the annotated value
            # But search_shows returns a list of model instances.
            # The 'weighted_distance' annotation should be on the instances.
            dist = getattr(r, 'weighted_distance', None)
            print(f" - {r.title} (Weighted Dist: {dist})")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    queries = [
        "modern western",
        "modern american western",
        "funny comedy movie",
        "action movie with Tom Cruise",
        "dark tv series about drugs"
    ]
    
    for q in queries:
        test_query(q)
