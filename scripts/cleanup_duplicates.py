import json
import os
import glob
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'recipes.json')

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    recipes = json.loads(f.read())

print(f"Total recipes before cleanup: {len(recipes)}")

# Keep only the NEWEST recipe for each unique title
seen_titles = {}
unique_recipes = []
removed_ids = []

for r in recipes:
    title = r.get("title_ja", "")
    if title not in seen_titles:
        seen_titles[title] = True
        unique_recipes.append(r)
    else:
        removed_ids.append(r["id"])
        print(f"  REMOVING duplicate: {r['id']} - {title}")

print(f"\nTotal recipes after cleanup: {len(unique_recipes)}")
print(f"Removed {len(removed_ids)} duplicates")

# Save cleaned data
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(unique_recipes, f, indent=2, ensure_ascii=False)

# Remove orphaned image files and HTML pages
for rid in removed_ids:
    img_path = os.path.join(BASE_DIR, 'recipes', f"{rid}.jpg")
    html_path = os.path.join(BASE_DIR, 'recipes_pages', f"{rid}.html")
    for path in [img_path, html_path]:
        if os.path.exists(path):
            os.remove(path)
            print(f"  Deleted: {path}")

print("\nCleanup complete!")
