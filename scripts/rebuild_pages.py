import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_recipe import load_recipes, generate_homepage, generate_individual_pages

recipes = load_recipes()
print(f"Rebuilding pages for {len(recipes)} recipes...")
generate_homepage(recipes)
generate_individual_pages(recipes)
print("Done!")
