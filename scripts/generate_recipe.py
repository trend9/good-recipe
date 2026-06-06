import os
import json
import random
import time
import urllib.parse
import requests
import re

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'recipes.json')
RECIPE_IMAGES_DIR = os.path.join(BASE_DIR, 'recipes')

os.makedirs(RECIPE_IMAGES_DIR, exist_ok=True)

# ============================================================
# LLM Recipe Generation via Hugging Face Inference API
# ============================================================

# Categories and random ingredients for LLM prompt variety
CATEGORIES = [
    ("noodle", "麺類"),
    ("dessert", "デザート"),
    ("side", "おかず"),
    ("bread", "パン類"),
    ("rice", "ご飯もの"),
    ("drink", "ドリンク"),
    ("snack", "おやつ"),
]

BIZARRE_COMBOS = [
    "コーラ × カレーライス", "わたあめ × ラーメン", "アイスクリーム × 納豆",
    "チョコレート × 餃子", "プリン × 醤油", "ポテトチップス × ヨーグルト",
    "メロンソーダ × 味噌汁", "マシュマロ × キムチ", "ジャム × 焼き魚",
    "コンデンスミルク × カップ麺", "バナナ × 醤油ラーメン", "キャラメル × 冷やし中華",
    "ホイップクリーム × 牛丼", "抹茶 × ピザ", "はちみつ × 唐揚げ",
    "ココア × おでん", "マヨネーズ × ホットケーキ", "グミ × お茶漬け",
    "ゼリー × カレーうどん", "チーズ × あんこ", "コーンフレーク × 豚汁",
    "タピオカ × 天ぷら", "クリームソーダ × そうめん", "杏仁豆腐 × キムチ鍋",
    "ドーナツ × 味噌", "パンケーキ × 明太子", "綿菓子 × たこ焼き",
    "プッチンプリン × 焼きそば", "練乳 × 肉じゃが", "ポッキー × 雑炊",
    "わさび × シュークリーム", "柿の種 × チョコフォンデュ",
    "エナジードリンク × そば", "ラムネ × 冷麺", "きなこ × ハンバーグ",
]

LLM_SYSTEM_PROMPT = """あなたは「あくまれしぴ」という奇抜レシピサイトの専属レシピクリエイターです。
SNSでバズるような、見た目のインパクトが強く、実際に作れる奇抜な組み合わせレシピを1つ考案してください。

以下のJSON形式で出力してください。JSON以外のテキストは一切出力しないでください。
```json
{
  "title_ja": "レシピ名（日本語）",
  "title_en": "Recipe Name (English)",
  "description_ja": "SNSでバズるような魅力的な説明文（日本語・50文字以上）",
  "description_en": "Attractive description in English",
  "category": "カテゴリ英語(noodle/dessert/side/bread/rice/drink/snack)",
  "category_ja": "カテゴリ日本語",
  "occasion_ja": "こんな時におすすめ！（日本語）",
  "occasion_en": "Recommended occasion (English)",
  "ingredients": [
    {"name": "材料名", "amount": "分量"},
    {"name": "材料名", "amount": "分量"}
  ],
  "steps": [
    "手順1の説明",
    "手順2の説明",
    "手順3の説明",
    "手順4の説明"
  ],
  "image_prompt": "Cozy anime illustration of the dish, detailed food digital art, Ghibli style (英語で具体的に料理の見た目を描写)"
}
```"""


def generate_recipe_with_llm(hf_token, existing_titles):
    """Use Hugging Face LLM to generate a unique bizarre recipe."""
    
    # Pick a random bizarre combo for inspiration
    combo = random.choice(BIZARRE_COMBOS)
    
    # Build user prompt with existing titles to avoid duplicates
    existing_list = "、".join(existing_titles[:10]) if existing_titles else "なし"
    
    user_prompt = f"""以下の奇抜な食材の組み合わせをヒントに、新しいレシピを1つ考えてください。
ヒントの組み合わせ: {combo}

既存のレシピ（重複禁止）: {existing_list}

上記と被らない、全く新しい奇抜レシピをJSON形式で出力してください。材料は4〜6個、手順は4つにしてください。"""

    # Try multiple LLM models in order of preference
    models = [
        "mistralai/Mistral-7B-Instruct-v0.3",
        "google/gemma-2-2b-it",
        "HuggingFaceH4/zephyr-7b-beta",
        "microsoft/Phi-3-mini-4k-instruct",
    ]
    
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }
    
    for model in models:
        print(f"Trying LLM model: {model}...")
        
        # Try chat completions API first
        chat_url = "https://router.huggingface.co/v1/chat/completions"
        chat_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.9,
            "stream": False
        }
        
        for attempt in range(1, 4):
            try:
                print(f"  Attempt {attempt}...")
                response = requests.post(chat_url, json=chat_payload, headers=headers, timeout=90)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"  LLM response length: {len(content)} chars")
                    
                    # Extract JSON from response
                    recipe_data = extract_json_from_text(content)
                    if recipe_data and validate_recipe(recipe_data):
                        print(f"  Successfully generated recipe: {recipe_data.get('title_ja', '?')}")
                        return recipe_data
                    else:
                        print(f"  Failed to parse valid JSON from response")
                        
                elif response.status_code == 503:
                    wait_time = response.json().get("estimated_time", 20)
                    print(f"  Model loading, waiting {wait_time}s...")
                    time.sleep(min(wait_time, 30))
                else:
                    print(f"  Error {response.status_code}: {response.text[:200]}")
                    
                    # Try text generation API as fallback
                    if attempt == 1:
                        print("  Trying text generation API instead...")
                        text_url = f"https://router.huggingface.co/hf-inference/models/{model}"
                        full_prompt = f"<s>[INST] {LLM_SYSTEM_PROMPT}\n\n{user_prompt} [/INST]"
                        text_payload = {
                            "inputs": full_prompt,
                            "parameters": {
                                "max_new_tokens": 1500,
                                "temperature": 0.9,
                                "return_full_text": False
                            }
                        }
                        try:
                            text_resp = requests.post(text_url, json=text_payload, headers=headers, timeout=90)
                            if text_resp.status_code == 200:
                                text_result = text_resp.json()
                                if isinstance(text_result, list) and len(text_result) > 0:
                                    generated = text_result[0].get("generated_text", "")
                                    recipe_data = extract_json_from_text(generated)
                                    if recipe_data and validate_recipe(recipe_data):
                                        print(f"  Successfully generated recipe via text API: {recipe_data.get('title_ja', '?')}")
                                        return recipe_data
                        except Exception as e:
                            print(f"  Text API fallback error: {e}")
                    
                    time.sleep(3)
            except Exception as e:
                print(f"  Request error: {type(e).__name__}: {e}")
                time.sleep(3)
    
    return None


def extract_json_from_text(text):
    """Extract JSON object from LLM response text."""
    # Try to find JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"title_ja"[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try finding the largest { ... } block
    brace_start = text.find('{')
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start:i+1])
                    except json.JSONDecodeError:
                        break
    
    return None


def validate_recipe(data):
    """Check that generated recipe has required fields."""
    required = ["title_ja", "title_en", "description_ja", "category", "category_ja", 
                "ingredients", "steps"]
    for field in required:
        if field not in data:
            print(f"  Missing required field: {field}")
            return False
    if not isinstance(data.get("ingredients"), list) or len(data["ingredients"]) < 2:
        print("  Not enough ingredients")
        return False
    if not isinstance(data.get("steps"), list) or len(data["steps"]) < 2:
        print("  Not enough steps")
        return False
    return True


# No fallback templates - all recipes must be generated by LLM


# ============================================================
# Data I/O
# ============================================================

def load_recipes():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except Exception as e:
            print(f"Error loading recipes: {e}")
            return []
    return []

def save_recipes(recipes):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(recipes, f, indent=2, ensure_ascii=False)


# ============================================================
# Static Page Generators
# ============================================================

def generate_individual_pages(recipes):
    articles_dir = os.path.join(BASE_DIR, 'recipes_pages')
    os.makedirs(articles_dir, exist_ok=True)
    
    for rp in recipes:
        rp_id = rp.get("id")
        filename = rp.get("filename")
        title_ja = rp.get("title_ja", "奇抜レシピ").replace('"', '&quot;')
        desc_ja = rp.get("description_ja", "").replace('"', '&quot;')
        category_ja = rp.get("category_ja", "その他").replace('"', '&quot;')
        occasion_ja = rp.get("occasion_ja", "").replace('"', '&quot;')
        date_str = rp.get("date", "")
        
        ingredients_list_html = ""
        ing_chunks = [rp["ingredients"][i:i + 3] for i in range(0, len(rp["ingredients"]), 3)]
        
        colors = ["yellow", "pink", "blue", "green"]
        for idx, chunk in enumerate(ing_chunks):
            color = colors[idx % len(colors)]
            items_html = ""
            for item in chunk:
                items_html += f'<li class="ingredient-item"><span>{item["name"]}</span><strong>{item["amount"]}</strong></li>'
            
            ingredients_list_html += f"""
            <div class="postit-note {color}">
              <h3>材料リスト {idx + 1}</h3>
              <ul class="ingredient-list">
                {items_html}
              </ul>
            </div>
            """
            
        steps_html = ""
        for idx, step in enumerate(rp["steps"]):
            steps_html += f"""
            <div class="step-card">
              <div class="step-num">{idx + 1}</div>
              <div class="step-content">{step}</div>
            </div>
            """

        schema_json = {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "name": title_ja,
            "image": [f"https://good-recipe.vercel.app/recipes/{filename}"],
            "author": {"@type": "Organization", "name": "Buzz Recipe Laboratory"},
            "datePublished": date_str.split(" ")[0] if date_str else "2026-06-06",
            "description": desc_ja,
            "recipeIngredient": [f"{item['name']} {item['amount']}" for item in rp["ingredients"]],
            "recipeInstructions": [{"@type": "HowToStep", "text": step} for step in rp["steps"]]
        }
        schema_script = f'<script type="application/ld+json">{json.dumps(schema_json, ensure_ascii=False)}</script>'
        
        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_ja} - あくまれしぴ</title>
  <meta name="description" content="{desc_ja}">
  
  <!-- Open Graph -->
  <meta property="og:title" content="{title_ja} - あくまれしぴ">
  <meta property="og:description" content="{desc_ja}">
  <meta property="og:image" content="https://good-recipe.vercel.app/recipes/{filename}">
  <meta property="og:type" content="article">
  
  <!-- CSS Link -->
  <link rel="stylesheet" href="../index.css">
  {schema_script}
</head>
<body>

  <!-- Header Navigation -->
  <header>
    <div class="nav-container">
      <a href="../" class="logo">
        <span class="logo-icon"></span>
        あくまれしぴ
      </a>
    </div>
  </header>

  <!-- Detail Content Section -->
  <main class="detail-main">
    <div class="recipe-header-card">
      <span class="recipe-detail-badge">{category_ja}</span>
      <h1 class="recipe-title-h1">{title_ja}</h1>
      <div class="recipe-meta-row">
        <span>投稿日: {date_str}</span>
        <span>難易度: カンタン ★☆☆</span>
      </div>
      <img class="recipe-detail-img" src="../recipes/{filename}" alt="{title_ja}">
      <div class="recipe-desc-box">
        <p>{desc_ja}</p>
      </div>
    </div>

    <!-- Occasion Box -->
    <div class="recommend-box">
      <h3 class="recommend-title">💡 こんな時・こんな人におすすめ！</h3>
      <p style="font-size: 0.95rem; color: var(--text-secondary);">{occasion_ja}</p>
    </div>

    <!-- Ingredients Board -->
    <h2 class="ingredients-title">📋 必要な材料（ポストイット風）</h2>
    <div class="ingredients-board">
      {ingredients_list_html}
    </div>

    <!-- Instructions -->
    <div class="instructions-section">
      <h2 class="ingredients-title" style="margin-top: 0; margin-bottom: 1.5rem;">🍳 作り方ステップ</h2>
      {steps_html}
    </div>

    <div style="text-align: center; margin-top: 2rem;">
      <a href="../" class="btn btn-primary">
        ホームに戻る
      </a>
    </div>
  </main>

  <!-- Footer -->
  <footer>
    <p>&copy; 2026 あくまれしぴ. All rights reserved.</p>
  </footer>

  <!-- Firebase Analytics Pageview Incrementor -->
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-database-compat.js"></script>
  <script>
    const firebaseConfig = {{
      apiKey: "AIzaSyDV5eL7wOP5xVgPfPFoC5LBBgI74LDT6l4",
      authDomain: "akuma-recipe.firebaseapp.com",
      projectId: "akuma-recipe",
      storageBucket: "akuma-recipe.firebasestorage.app",
      messagingSenderId: "963604937462",
      appId: "1:963604937462:web:ead8d17eb9e1f3e52acad7",
      measurementId: "G-8DC8SENZWL"
    }};
    if (!firebase.apps.length) {{
      firebase.initializeApp(firebaseConfig);
    }}
    // Increment pageview for this recipe id
    const recipeId = "{rp_id}";
    firebase.database().ref('pageviews/' + recipeId).transaction(currentValue => {{
      return (currentValue || 0) + 1;
    }});
  </script>
</body>
</html>
"""
        filepath = os.path.join(articles_dir, f"{rp_id}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    print(f"Generated {len(recipes)} individual recipe detail pages.")

def generate_homepage(recipes):
    cards_html = ""
    for idx, rp in enumerate(recipes):
        rp_id = rp.get("id")
        filename = rp.get("filename")
        title_ja = rp.get("title_ja")
        desc_ja = rp.get("description_ja")
        category_ja = rp.get("category_ja")
        date_str = rp.get("date")
        
        color_class = f"color-{idx % 6}"
        
        cards_html += f"""
      <a href="recipes_pages/{rp_id}.html" class="recipe-card {color_class}">
        <span class="card-badge">{category_ja}</span>
        <div class="card-img-wrapper">
          <img class="card-img" src="recipes/{filename}" alt="{title_ja}" loading="lazy">
        </div>
        <h2 class="card-title">{title_ja}</h2>
        <p class="card-hook">{desc_ja}</p>
        <div class="card-footer">
          <span>{date_str.split(" ")[0]}</span>
          <span>詳細を見る &rarr;</span>
        </div>
      </a>"""

    homepage_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>あくまれしぴ - 1日24個投稿される奇抜アレンジレシピの聖地</title>
  <meta name="description" content="クックパッドを超える新感覚！SNSで絶対バズる奇抜で美味しい料理レシピを大公開。ポストイット風の見やすい材料リストと美味しそうなアニメ調フード画像が満載。">
  
  <!-- CSS Link -->
  <link rel="stylesheet" href="index.css">
</head>
<body>

  <!-- Header Navigation -->
  <header>
    <div class="nav-container">
      <a href="#" class="logo">
        <span class="logo-icon"></span>
        あくまれしぴ
      </a>
    </div>
  </header>

  <!-- Hero Banner -->
  <section style="text-align: center; padding: 4rem 1rem 2rem; background: linear-gradient(180deg, #fff9db 0%, var(--bg-color) 100%);">
    <h1 style="font-family: 'Kiwi Maru', sans-serif; font-size: 2.5rem; color: #c92a2a; margin-bottom: 1rem;">
      😈 あくまれしぴ - 奇抜アレンジレシピの聖地
    </h1>
    <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto 1.5rem; font-size: 1.1rem;">
      女の子ウケ抜群 of パステル付箋風デザイン。ローカルAIが描き下ろした最高にエモいアニメ調フード画像と共にお届け。
    </p>
  </section>

  <!-- Main Recipes Gallery -->
  <main class="gallery-section">
    <div class="gallery-grid" id="recipe-grid">
      {cards_html}
    </div>
  </main>

  <!-- Footer -->
  <footer>
    <p>&copy; 2026 あくまれしぴ. All rights reserved.</p>
  </footer>
</body>
</html>
"""
    
    with open(os.path.join(BASE_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(homepage_html)
    print("Successfully rebuilt index.html listing!")


# ============================================================
# Image Generation
# ============================================================

def generate_image(prompt, filepath, filename, hf_token):
    """Try multiple image generation APIs, return True on success."""
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(0, 999999)
    success = False
    
    # 1. Hugging Face Inference API - try multiple image models
    if hf_token:
        hf_image_models = [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "runwayml/stable-diffusion-v1-5",
        ]
        hf_headers = {"Authorization": f"Bearer {hf_token}"}
        
        for hf_model in hf_image_models:
            print(f"Attempting HF image model: {hf_model}")
            hf_url = f"https://router.huggingface.co/hf-inference/models/{hf_model}"
            
            for attempt in range(1, 4):
                try:
                    print(f"  Attempt {attempt}...")
                    response = requests.post(hf_url, json={"inputs": prompt}, headers=hf_headers, timeout=90)
                    if response.status_code == 200 and len(response.content) > 5000:
                        content_type = response.headers.get('content-type', '')
                        if 'image' in content_type or len(response.content) > 10000:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            print(f"  SUCCESS! Saved {filename} ({len(response.content)} bytes, model={hf_model})")
                            return True
                    elif response.status_code == 503:
                        wait = min(response.json().get("estimated_time", 15), 25)
                        print(f"  Model loading, waiting {wait}s...")
                        time.sleep(wait)
                    elif response.status_code == 422:
                        print(f"  Model {hf_model} rejected input, trying next model...")
                        break
                    else:
                        print(f"  Error {response.status_code}: {response.text[:200]}")
                        time.sleep(3)
                except Exception as e:
                    print(f"  Request failed: {type(e).__name__}")
                    time.sleep(3)
                
    # 2. Pollinations AI Fallback (free tier)
    if not success:
        print("Falling back to Pollinations AI...")
        pollinations_params_list = [
            f"?width=768&height=768&nologo=true&seed={seed}&enhance=true",
            f"?width=512&height=512&nologo=true&seed={seed}",
        ]
        
        for params in pollinations_params_list:
            url_attempt = f"https://image.pollinations.ai/prompt/{encoded_prompt}{params}"
            print(f"  Querying: {url_attempt[:120]}...")
            for attempt in range(1, 4):
                try:
                    response = requests.get(url_attempt, timeout=120, allow_redirects=True)
                    content_type = response.headers.get('content-type', '')
                    if response.status_code == 200 and ('image' in content_type or len(response.content) > 10000):
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        print(f"  Saved Pollinations image! ({len(response.content)} bytes)")
                        return True
                    else:
                        print(f"  Failed: code={response.status_code}, size={len(response.content)}")
                        time.sleep(5)
                except Exception as e:
                    print(f"  Pollinations error: {e}")
                    time.sleep(5)
            
    # 3. Hercai Anime generator fallback
    if not success:
        print("Falling back to Hercai...")
        for model in ["v3", "simurg", "lexica"]:
            herc_url = f"https://hercai.onrender.com/{model}/text2image"
            for attempt in range(1, 3):
                try:
                    response = requests.get(herc_url, params={"prompt": prompt}, timeout=60)
                    if response.status_code == 200:
                        img_url = response.json().get("url")
                        if img_url:
                            img_data = requests.get(img_url, timeout=60)
                            if img_data.status_code == 200 and len(img_data.content) > 5000:
                                with open(filepath, 'wb') as f:
                                    f.write(img_data.content)
                                print(f"  Saved Hercai image!")
                                return True
                    time.sleep(3)
                except Exception as e:
                    print(f"  Hercai error: {e}")
                    time.sleep(3)

    # 4. PIL Programmatic fallback
    if not success:
        print("All APIs failed. Generating fallback image with PIL...")
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
        except ImportError:
            import subprocess
            subprocess.run(["pip", "install", "pillow"], check=True)
            from PIL import Image, ImageDraw, ImageFont, ImageFilter

        img = Image.new('RGB', (800, 800), color='#fff9db')
        draw = ImageDraw.Draw(img)
        
        for y in range(800):
            r = int(255 - (y / 800) * 30)
            g = int(245 - (y / 800) * 60)
            b = int(220 - (y / 800) * 100)
            draw.line([(0, y), (800, y)], fill=(r, g, b))
        
        draw.ellipse([(100, 150), (700, 650)], fill='#fff5f5', outline='#e8590c', width=6)
        draw.ellipse([(150, 200), (650, 600)], fill='#fff9db', outline='#fcc419', width=4)
        
        food_colors = ['#ff6b6b', '#51cf66', '#ffa94d', '#845ef7', '#339af0']
        for i in range(8):
            cx, cy = random.randint(250, 550), random.randint(280, 520)
            size = random.randint(30, 70)
            draw.ellipse([(cx-size, cy-size), (cx+size, cy+size)], fill=random.choice(food_colors), outline='#fff', width=2)
        
        draw.rectangle([(50, 660), (750, 780)], fill='#c92a2a', outline='#a61e1e', width=3)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text((200, 50), "AKUMA RECIPE", fill="#c92a2a", font=font_large)
        
        img = img.filter(ImageFilter.SMOOTH)
        img.save(filepath, "JPEG", quality=90)
        print(f"  Saved PIL fallback image!")
        return True

    return False


# ============================================================
# Main
# ============================================================

def main():
    existing_recipes = load_recipes()
    existing_titles = [r.get("title_ja", "") for r in existing_recipes]
    
    timestamp = int(time.time())
    recipe_id = f"recipe_{timestamp}"
    filename = f"recipe_{timestamp}.jpg"
    filepath = os.path.join(RECIPE_IMAGES_DIR, filename)
    
    hf_token = os.environ.get('HF_TOKEN')
    
    # Step 1: Generate recipe content with LLM
    recipe_data = None
    if hf_token:
        print("=" * 60)
        print("STEP 1: Generating recipe with Hugging Face LLM...")
        print("=" * 60)
        recipe_data = generate_recipe_with_llm(hf_token, existing_titles)
    
    # If LLM fails, abort - no templates allowed
    if not recipe_data:
        print("ERROR: LLM recipe generation failed and no HF_TOKEN available.")
        print("Cannot create recipe without LLM. Aborting.")
        return
    
    # Ensure required fields have defaults
    if "occasion_ja" not in recipe_data:
        recipe_data["occasion_ja"] = "友達との楽しい食事会や、SNSで話題になりたい時に！"
    if "occasion_en" not in recipe_data:
        recipe_data["occasion_en"] = "For fun dinner parties or when you want to go viral on social media!"
    if "description_en" not in recipe_data:
        recipe_data["description_en"] = recipe_data.get("title_en", recipe_data["title_ja"])
    
    # Get image prompt from recipe data
    image_prompt = recipe_data.get("image_prompt") or recipe_data.get("prompt", "")
    if not image_prompt:
        # Generate a default prompt from the title
        image_prompt = f"Cozy anime illustration of {recipe_data.get('title_en', recipe_data['title_ja'])}, delicious food aesthetic, detailed digital art, Ghibli style, warm lighting"
    
    print(f"\nRecipe: {recipe_data['title_ja']}")
    print(f"Image prompt: {image_prompt[:100]}...")
    
    # Step 2: Generate image
    print("\n" + "=" * 60)
    print("STEP 2: Generating image...")
    print("=" * 60)
    
    img_success = generate_image(image_prompt, filepath, filename, hf_token)
    
    if img_success:
        new_recipe = {
            "id": recipe_id,
            "category": recipe_data.get("category", "side"),
            "category_ja": recipe_data.get("category_ja", "おかず"),
            "title_ja": recipe_data["title_ja"],
            "title_en": recipe_data.get("title_en", recipe_data["title_ja"]),
            "description_ja": recipe_data["description_ja"],
            "description_en": recipe_data.get("description_en", ""),
            "occasion_ja": recipe_data.get("occasion_ja", ""),
            "occasion_en": recipe_data.get("occasion_en", ""),
            "ingredients": recipe_data["ingredients"],
            "steps": recipe_data["steps"],
            "prompt": image_prompt,
            "filename": filename,
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "timestamp": timestamp,
            "likes": 0,
            "views": random.randint(150, 480)
        }
        
        existing_recipes.insert(0, new_recipe)
        save_recipes(existing_recipes)
        print("\nUpdated recipes database successfully!")
        
        generate_individual_pages(existing_recipes)
        generate_homepage(existing_recipes)
        
        print(f"\n{'=' * 60}")
        print(f"SUCCESS: {recipe_data['title_ja']}")
        print(f"{'=' * 60}")
    else:
        print("ERROR: Image generation completely failed.")

if __name__ == "__main__":
    main()
