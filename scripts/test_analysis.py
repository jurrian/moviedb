
import os
import sys
import django
from pprint import pprint

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from movies.search import search_shows, analyze_search_result

def test_analysis(query):
    print(f"\n--- Testing Analysis for: '{query}' ---")
    try:
        results, structured = search_shows(query, top_k=1)
        if not results:
            print("No results found.")
            return

        show = results[0]
        print(f"Top Result: {show.title}")
        
        # Mock component dists (extract from object)
        comp_dists = {}
        fields = ["plot", "cast", "genre", "tow", "tags", "meta", "language", "main"]
        for k in fields:
            attr = f"dist_{k}"
            if hasattr(show, attr):
                val = getattr(show, attr)
                comp_dists[k] = val if val is not None else 2.0
                
        print("asking AI...")
        analysis = analyze_search_result(query, show, structured, comp_dists)
        print("\n=== AI ANALYSIS ===\n")
        print(analysis)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis("modern western")
