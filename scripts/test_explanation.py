
import os
import sys
import django
from pprint import pprint

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from movies.search import search_shows

def test_explanation(query):
    print(f"\n--- Testing Query: '{query}' ---")
    try:
        results, structured = search_shows(query, top_k=3)
        print("Parsed Weights:")
        pprint(structured.get("weights", {}))
        
        for r in results:
            print(f"\nTitle: {r.title}")
            print(f"Total Weighted Dist: {r.weighted_distance}")
            print(f" - Dist Plot: {getattr(r, 'dist_plot', 'N/A')}")
            print(f" - Dist Cast: {getattr(r, 'dist_cast', 'N/A')}")
            print(f" - Dist Genre: {getattr(r, 'dist_genre', 'N/A')}")
            print(f" - Dist Tone: {getattr(r, 'dist_tone', 'N/A')}")
            print(f" - Dist Main: {getattr(r, 'dist_main', 'N/A')}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_explanation("funny comedy movie from 90s")
