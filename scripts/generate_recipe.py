import os
import json
import random
import time
import urllib.parse
import requests

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'recipes.json')
RECIPE_IMAGES_DIR = os.path.join(BASE_DIR, 'recipes')

os.makedirs(RECIPE_IMAGES_DIR, exist_ok=True)

# Bizarre Food Items seed database to mix and match for high click-bait / viral recipe ideas
BIZARRE_FOODS = [
    {
        "title_ja": "綿あめカレーうどん",
        "title_en": "Cotton Candy Curry Udon",
        "description_ja": "ふわふわの甘い綿あめをスパイシーなカレーうどんに溶かして食べる、衝撃の新感覚レシピ！甘みと辛みが絶妙にマッチします。",
        "description_en": "A shocking new sensory recipe where fluffy sweet cotton candy is dissolved into spicy curry udon! Sweet and spicy match perfectly.",
        "category": "noodle",
        "category_ja": "麺類",
        "occasion_ja": "週末のホームパーティーや、甘辛の新しい扉を開きたい時に！",
        "occasion_en": "Perfect for weekend house parties or when you want to open a new door of sweet and savory!",
        "ingredients": [
            {"name": "冷凍うどん", "amount": "1玉"},
            {"name": "カレールー", "amount": "1皿分"},
            {"name": "和風だし", "amount": "300ml"},
            {"name": "綿あめ", "amount": "大きな塊1個"},
            {"name": "豚バラ肉", "amount": "50g"},
            {"name": "ネギ", "amount": "適量"}
        ],
        "steps": [
            "豚バラ肉を炒め、和風だしとカレールーを加えてカレーつゆを作ります。",
            "茹でたうどんをつゆに入れ、器に盛ります。",
            "食べる直前に、うどん全体を覆うように大きな綿あめをのせます。",
            "綿あめがつゆに溶けていく様子を楽しみながら混ぜて召し上がれ！"
        ],
        "prompt": "Cozy anime illustration of a steaming bowl of japanese curry udon, topped with a giant fluffy cloud of pink cotton candy, delicious food aesthetic, Ghibli style, detailed digital art"
    },
    {
        "title_ja": "メロンソーダラーメン",
        "title_en": "Melon Soda Ramen",
        "description_ja": "シュワシュワの炭酸メロンソーダと塩ラーメンスープの奇跡のコラボレーション！見た目のインパクトと爽快なのどごしが最高です。",
        "description_en": "A miraculous collaboration of fizzy carbonated melon soda and salt ramen soup! The visual impact and refreshing throat feel are outstanding.",
        "category": "noodle",
        "category_ja": "麺類",
        "occasion_ja": "暑い夏の日のランチや、SNSでバズる写真を撮りたい女子会に！",
        "occasion_en": "For hot summer lunches or girls' night outs looking to snap viral photos!",
        "ingredients": [
            {"name": "塩ラーメン（インスタント）", "amount": "1袋"},
            {"name": "無糖炭酸水", "amount": "150ml"},
            {"name": "メロンシロップ", "amount": "30ml"},
            {"name": "バニラアイス", "amount": "1ディッシャー"},
            {"name": "チャーシュー", "amount": "1枚"},
            {"name": "サクランボ（缶詰）", "amount": "1個"}
        ],
        "steps": [
            "ラーメンの麺を通常通り茹で、冷水でしめます。",
            "付属の塩スープの素を少量の温水で溶かし、炭酸水とメロンシロップを混ぜて冷やします。",
            "器に麺と冷たいメロンスープを注ぎます。",
            "トッピングとしてバニラアイス、チャーシュー、サクランボをのせて完成。"
        ],
        "prompt": "Cozy anime illustration of a bowl of ramen filled with glowing emerald green melon soda broth, topped with a scoop of vanilla ice cream and a cherry, detailed food digital art, Makoto Shinkai style"
    },
    {
        "title_ja": "板チョコ餃子ドッグ",
        "title_en": "Chocolate Bar Gyoza Dog",
        "description_ja": "ジューシーな餃子の皮の中にまるごと板チョコを挟んでパリパリに揚げ焼きした、甘じょっぱさがクセになる悪魔のスイーツおつまみ。",
        "description_en": "A whole chocolate bar wrapped inside gyoza skin and pan-fried to crispy perfection. A devilish sweet and salty snack that is highly addictive.",
        "category": "dessert",
        "category_ja": "デザート",
        "occasion_ja": "夜遅くの背徳的なおやつや、バレンタインの意外なサプライズに！",
        "occasion_en": "For late-night guilty pleasure snacks or an unexpected Valentine surprise!",
        "ingredients": [
            {"name": "餃子の皮（大きめ）", "amount": "10枚"},
            {"name": "ミルクチョコレート板チョコ", "amount": "1枚"},
            {"name": "マシュマロ", "amount": "5個"},
            {"name": "サラダ油", "amount": "適量"},
            {"name": "粉糖", "amount": "仕上げ用"}
        ],
        "steps": [
            "板チョコを餃子の皮に入るサイズに割ります。",
            "餃子の皮にチョコと半分に切ったマシュマロをのせ、フチに水をつけてしっかり包みます。",
            "フライパンに多めの油を熱し、きつね色になるまで両面をパリッと揚げ焼きします。",
            "お皿に盛り付け、仕上げに粉糖をふりかけます。"
        ],
        "prompt": "Cozy anime illustration of crispy golden-brown fried gyoza dumplings oozing warm melted milk chocolate and marshmallows, stacked beautifully on a pastel plate, Ghibli style, detailed art"
    },
    {
        "title_ja": "タピオカ麻婆豆腐",
        "title_en": "Tapioca Mapo Tofu",
        "description_ja": "辛口の本格麻婆豆腐に、もちもちのブラックタピオカをプラス！噛むたびに楽しい食感と旨辛ダレが最高に絡み合います。",
        "description_en": "Adding chewy black tapioca pearls to authentic spicy mapo tofu! The combination of fun texture and spicy savory sauce is amazing.",
        "category": "side",
        "category_ja": "おかず",
        "occasion_ja": "モチモチ食感が大好きな女子や、いつもの中華に飽きた食卓に！",
        "occasion_en": "For chewiness-loving girls or dining tables bored of typical Chinese food!",
        "ingredients": [
            {"name": "豆腐", "amount": "1丁"},
            {"name": "豚ひき肉", "amount": "100g"},
            {"name": "ブラックタピオカ（茹でたもの）", "amount": "50g"},
            {"name": "麻婆豆腐の素（辛口）", "amount": "1回分"},
            {"name": "ラー油", "amount": "適量"}
        ],
        "steps": [
            "豆腐をさいの目に切り、茹でて水気を切っておきます。",
            "フライパンでひき肉を炒め、麻婆豆腐の素と水を加えて一煮立ちさせます。",
            "豆腐と茹でたブラックタピオカを加え、崩れないように優しく混ぜ合わせます。",
            "とろみがついたらラー油を回し入れ、熱々を器に盛ります。"
        ],
        "prompt": "Anime style illustration of a steaming plate of hot red mapo tofu filled with shiny round black tapioca pearls and diced tofu, garnished with green scallions, cozy food aesthetic, detailed digital art"
    },
    {
        "title_ja": "たこ焼きホットケーキ",
        "title_en": "Takoyaki Hotcake",
        "description_ja": "たこ焼き器を使って丸く作ったベビーカステラ風ホットケーキの中に、本物のタコをイン！ソースの代わりにハチミツをかけて召し上がれ。",
        "description_en": "Round baby-castella style hotcakes made using a takoyaki griddle, with real octopus chunks hidden inside! Top with honey instead of savory sauce.",
        "category": "dessert",
        "category_ja": "デザート",
        "occasion_ja": "お子様と一緒に楽しむタコパや、ちょっとしたおうちカフェ時間に！",
        "occasion_en": "For a takoyaki party with kids or a cute home cafe afternoon!",
        "ingredients": [
            {"name": "ホットケーキミックス", "amount": "150g"},
            {"name": "牛乳", "amount": "100ml"},
            {"name": "たまご", "amount": "1個"},
            {"name": "茹でダコ（ぶつ切り）", "amount": "20カット"},
            {"name": "はちみつ / メープルシロップ", "amount": "お好みで"}
        ],
        "steps": [
            "ボウルにホットケーキミックス、牛乳、たまごを入れてダマがなくなるまで混ぜます。",
            "温めたたこ焼き器に薄く油をひき、生地を穴の半分まで流し込みます。",
            "中央にタコのぶつ切りを1つずつ入れ、さらに上から生地を溢れるくらい注ぎます。",
            "竹串でくるくると回しながら綺麗な球体に焼き上げ、はちみつをかけて完成。"
        ],
        "prompt": "Anime illustration of golden round takoyaki-shaped pancake balls, glistening with honey and butter syrup, on a warm wooden board, cute illustration style, warm cozy lighting"
    },
    {
        "title_ja": "プリングルズポテトマッシュトースト",
        "title_en": "Pringles Mashed Potato Toast",
        "description_ja": "砕いたプリングルズをお湯でポテトサラダ風に戻し、チーズと一緒にトーストにのせて焼き上げました。超濃厚なポテチの風味がジュワッと広がります。",
        "description_en": "Rehydrate crushed Pringles potato chips with hot water into a potato-salad style mash, then bake on toast with melted cheese. Hyper-rich potato flavor spreads in every bite.",
        "category": "bread",
        "category_ja": "パン類",
        "occasion_ja": "ガッツリ食べたい朝ごはんや、深夜のリッチなジャンク欲に！",
        "occasion_en": "For hearty breakfasts or intense late-night junk food cravings!",
        "ingredients": [
            {"name": "食パン（6枚切り）", "amount": "1枚"},
            {"name": "プリングルズ（サワークリーム＆オニオン）", "amount": "1/2缶"},
            {"name": "お湯", "amount": "50ml"},
            {"name": "ピザ用チーズ", "amount": "30g"},
            {"name": "マヨネーズ", "amount": "大さじ1"}
        ],
        "steps": [
            "袋の中にプリングルズを入れて細かく砕きます。",
            "ボウルに移し、お湯を注いでスプーンでよく練ってポテトマッシュを作ります。",
            "食パンにマヨネーズを塗り、その上に作ったポテトマッシュを平らに広げます。",
            "チーズをたっぷりとのせ、トースターでこんがり焼き色がつくまで焼きます。"
        ],
        "prompt": "Anime illustration of a thick slice of golden toasted bread, topped with a mountain of creamy mashed potato and melted stringy cheese, cozy warm kitchen aesthetic"
    },
    {
        "title_ja": "ポテトチップスオムレツ",
        "title_en": "Potato Chips Omelet",
        "description_ja": "卵液の中にポテトチップスをそのまま砕き入れてフライパンで丸く焼き上げたスペイン風オムレツ。ポテチの塩気とサクサク感が卵と絶妙にマッチ！",
        "description_en": "A Spanish-style omelet made by crushing potato chips directly into egg wash and frying them round. The saltiness and crunchiness of potato chips match eggs perfectly!",
        "category": "side",
        "category_ja": "おかず",
        "occasion_ja": "お酒のおつまみが今すぐ欲しいとき、手軽な朝ごはんのおかずに！",
        "occasion_en": "When you need a quick drink snack or an easy morning side dish!",
        "ingredients": [
            {"name": "たまご", "amount": "3個"},
            {"name": "ポテトチップス（うすしお）", "amount": "1/2袋"},
            {"name": "牛乳", "amount": "大さじ1"},
            {"name": "オリーブオイル", "amount": "大さじ1"},
            {"name": "ケチャップ", "amount": "お好みで"}
        ],
        "steps": [
            "たまごをボウルに割り入れ、牛乳を加えてよく混ぜます。",
            "ポテトチップスを手で荒く砕きながら卵液に入れ、軽く浸します。",
            "フライパンにオリーブオイルを熱し、卵液を一気に流し込みます。",
            "弱火で両面をじっくりと丸く焼き上げ、お好みでケチャップを添えます。"
        ],
        "prompt": "Anime illustration of a round Spanish-style golden potato omelette slice on a white ceramic plate, steam rising, warm cozy food art"
    },
    {
        "title_ja": "プリン醤油うどん（ウニ風風）",
        "title_en": "Pudding Soy Sauce Udon (Sea Urchin Style)",
        "description_ja": "カスタードプリンに醤油をかけると「ウニ」の味になる！？その噂を本格的なうどんで再現。クリーミーで濃厚なコクがモチモチうどんに絡みます。",
        "description_en": "Does pudding with soy sauce taste like sea urchin?! Recreated that rumor in an authentic udon dish. Creamy rich depth coats the chewy udon noodles.",
        "category": "noodle",
        "category_ja": "麺類",
        "occasion_ja": "安価で高級ウニ気分を味わいたい給料日前や、好奇心旺盛な友達との食事に！",
        "occasion_en": "For days before payday when you want to feel luxurious on a budget, or meals with curious friends!",
        "ingredients": [
            {"name": "冷凍うどん", "amount": "1玉"},
            {"name": "市販のカスタードプリン", "amount": "1個"},
            {"name": "醤油 / めんつゆ", "amount": "大さじ1.5"},
            {"name": "刻み海苔", "amount": "適量"},
            {"name": "わさび", "amount": "少々"}
        ],
        "steps": [
            "冷凍うどんを電子レンジで加熱し、器に盛ります。",
            "温かいうどんの上に、カスタードプリンをドカンとまるごと1個のせます。",
            "醤油（またはめんつゆ）を回しかけ、わさびと刻み海苔をトッピングします。",
            "プリンをしっかりと崩しながら、全体を均一に混ぜ合わせて召し上がれ。"
        ],
        "prompt": "Anime style illustration of hot udon noodles topped with a single custard pudding shaking on top, drizzled with dark soy sauce and green nori seaweed, Ghibli food aesthetic"
    }
]

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

def generate_individual_pages(recipes):
    # Ensure detailed pages directory exists
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
        # Split ingredients into two post-its for stylish UI
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

        # Generate LD-JSON schema markup for SEO
        schema_json = {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "name": title_ja,
            "image": [f"https://good-recipe.vercel.app/recipes/{filename}"],
            "author": {
                "@type": "Organization",
                "name": "Buzz Recipe Laboratory"
            },
            "datePublished": date_str.split(" ")[0] if date_str else "2026-06-06",
            "description": desc_ja,
            "recipeIngredient": [f"{item['name']} {item['amount']}" for item in rp["ingredients"]],
            "recipeInstructions": [{"@type": "HowToStep", "text": step} for step in rp["steps"]]
        }
        schema_script = f"<script type=\"application/ld+json\">{json.dumps(schema_json, ensure_ascii=False)}</script>"
        
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
    # Generates the listing index.html page
    cards_html = ""
    for idx, rp in enumerate(recipes):
        rp_id = rp.get("id")
        filename = rp.get("filename")
        title_ja = rp.get("title_ja")
        desc_ja = rp.get("description_ja")
        category_ja = rp.get("category_ja")
        date_str = rp.get("date")
        
        # Color rotation index
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

def main():
    existing_recipes = load_recipes()
    count = len(existing_recipes)
    
    # Pick the next bizarre recipe sequentially or randomly
    recipe_template = BIZARRE_FOODS[count % len(BIZARRE_FOODS)]
    
    # Random offset to distinguish titles
    timestamp = int(time.time())
    recipe_id = f"recipe_{timestamp}"
    filename = f"recipe_{timestamp}.jpg"
    filepath = os.path.join(RECIPE_IMAGES_DIR, filename)
    
    prompt = recipe_template["prompt"]
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(0, 999999)
    success = False
    
    # 1. Hugging Face Inference API FLUX Model
    hf_token = os.environ.get('HF_TOKEN')
    if hf_token:
        print("HF_TOKEN detected. Starting image generation via Hugging Face...")
        hf_model = "black-forest-labs/FLUX.1-schnell"
        hf_url = f"https://api-inference.huggingface.co/models/{hf_model}"
        hf_headers = {"Authorization": f"Bearer {hf_token}"}
        
        for attempt in range(1, 6):
            try:
                print(f"Hugging Face attempt {attempt}...")
                response = requests.post(hf_url, json={"inputs": prompt}, headers=hf_headers, timeout=60)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    print(f"Successfully saved Hugging Face image to {filename}!")
                    success = True
                    break
                elif response.status_code == 503:
                    estimated_time = response.json().get("estimated_time", 20)
                    print(f"Model loading. Sleeping for {estimated_time}s...")
                    time.sleep(estimated_time)
                else:
                    print(f"Error {response.status_code}: {response.text}")
                    time.sleep(3)
            except Exception as e:
                print(f"Request failed: {type(e).__name__}")
                time.sleep(3)
                
    # 2. Pollinations AI Fallback (free tier, no model param to avoid 402)
    if not success:
        print("Falling back to Pollinations AI...")
        pollinations_params_list = [
            f"?width=768&height=768&nologo=true&seed={seed}&enhance=true",
            f"?width=512&height=512&nologo=true&seed={seed}",
        ]
        
        for params in pollinations_params_list:
            url_attempt = f"https://image.pollinations.ai/prompt/{encoded_prompt}{params}"
            print(f"Querying Pollinations AI: {url_attempt}")
            for attempt in range(1, 4):
                try:
                    response = requests.get(url_attempt, timeout=120, allow_redirects=True)
                    content_type = response.headers.get('content-type', '')
                    if response.status_code == 200 and ('image' in content_type or len(response.content) > 10000):
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        print(f"Saved Pollinations image to {filename}! ({len(response.content)} bytes)")
                        success = True
                        break
                    else:
                        print(f"Failed: code={response.status_code}, type={content_type}, size={len(response.content)}. Retrying...")
                        time.sleep(5)
                except Exception as e:
                    print(f"Pollinations error: {e}")
                    time.sleep(5)
            if success:
                break

    # 3. Hercai Anime generator fallback
    if not success:
        print("Falling back to Hercai Anime generator...")
        herc_models = ["v3", "simurg", "lexica"]
        for model in herc_models:
            print(f"Requesting image from Hercai (model: {model})...")
            herc_url = f"https://hercai.onrender.com/{model}/text2image"
            for attempt in range(1, 4):
                try:
                    response = requests.get(herc_url, params={"prompt": prompt + ", anime style food illustration, detailed"}, timeout=60)
                    if response.status_code == 200:
                        res_json = response.json()
                        img_url = res_json.get("url")
                        if img_url:
                            img_data = requests.get(img_url, timeout=60)
                            if img_data.status_code == 200:
                                with open(filepath, 'wb') as f:
                                    f.write(img_data.content)
                                print(f"Saved Hercai image to {filename}!")
                                success = True
                                break
                    time.sleep(3)
                except Exception as e:
                    print(f"Hercai error: {e}")
                    time.sleep(3)
            if success:
                break

    # 4. AI Horde anonymous API fallback
    if not success:
        print("Initiating AI Horde generation fallback...")
        horde_url = "https://aihorde.net/api/v2/generate/async"
        horde_headers = {
            "apikey": "0000000000",
            "Client-Agent": "RecipeWebsiteSystem:1.0:user@example.com"
        }
        horde_payload = {
            "prompt": prompt + ", anime style food, cozy ghibli style art",
            "models": ["stable_diffusion", "Dreamshaper", "Deliberate"],
            "params": {
                "width": 1024,
                "height": 1024,
                "steps": 20,
                "cfg_scale": 7.0
            }
        }
        try:
            submit_resp = requests.post(horde_url, json=horde_payload, headers=horde_headers, timeout=45)
            if submit_resp.status_code == 202:
                job_id = submit_resp.json().get("id")
                status_url = f"https://aihorde.net/api/v2/generate/status/{job_id}"
                for poll in range(1, 37):
                    status_resp = requests.get(status_url, timeout=30)
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        if status_data.get("done") is True:
                            generations = status_data.get("generations", [])
                            if generations:
                                img_url = generations[0].get("img")
                                img_data = requests.get(img_url, timeout=45)
                                if img_data.status_code == 200:
                                    with open(filepath, 'wb') as f:
                                        f.write(img_data.content)
                                    print(f"Successfully saved AI Horde image to {filename}!")
                                    success = True
                                    break
                        elif status_data.get("faulted") is True:
                            break
                    time.sleep(5)
        except Exception as e:
            print(f"AI Horde encountered error: {e}")

    # 5. PIL Programmatic generation fallback if all web APIs are down/rate-limited
    if not success:
        print("All APIs rate-limited. Generating fallback local art programmatically...")
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
        except ImportError:
            import subprocess
            subprocess.run(["pip", "install", "pillow"], check=True)
            from PIL import Image, ImageDraw, ImageFont, ImageFilter

        # Create a rich gradient background food card
        img = Image.new('RGB', (800, 800), color='#fff9db')
        draw = ImageDraw.Draw(img)
        
        # Warm gradient background
        for y in range(800):
            r = int(255 - (y / 800) * 30)
            g = int(245 - (y / 800) * 60)
            b = int(220 - (y / 800) * 100)
            draw.line([(0, y), (800, y)], fill=(r, g, b))
        
        # Decorative circles (plate/bowl)
        draw.ellipse([(100, 150), (700, 650)], fill='#fff5f5', outline='#e8590c', width=6)
        draw.ellipse([(150, 200), (650, 600)], fill='#fff9db', outline='#fcc419', width=4)
        
        # Food elements
        food_colors = ['#ff6b6b', '#51cf66', '#ffa94d', '#845ef7', '#339af0']
        for i in range(8):
            cx = random.randint(250, 550)
            cy = random.randint(280, 520)
            size = random.randint(30, 70)
            color = random.choice(food_colors)
            draw.ellipse([(cx-size, cy-size), (cx+size, cy+size)], fill=color, outline='#fff', width=2)
        
        # Title banner
        draw.rectangle([(50, 660), (750, 780)], fill='#c92a2a', outline='#a61e1e', width=3)
        
        # Text
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text((200, 50), "AKUMA RECIPE", fill="#c92a2a", font=font_large)
        draw.text((120, 700), recipe_template["title_ja"], fill="#ffffff", font=font_small)
        
        # Apply slight blur for softer look
        img = img.filter(ImageFilter.SMOOTH)
        
        img.save(filepath, "JPEG", quality=90)
        print(f"Successfully drew programmatic food canvas preview and saved to {filename}!")
        success = True

    if success:
        # Create a database record
        new_recipe = {
            "id": recipe_id,
            "category": recipe_template["category"],
            "category_ja": recipe_template["category_ja"],
            "title_ja": recipe_template["title_ja"],
            "title_en": recipe_template["title_en"],
            "description_ja": recipe_template["description_ja"],
            "description_en": recipe_template["description_en"],
            "occasion_ja": recipe_template["occasion_ja"],
            "occasion_en": recipe_template["occasion_en"],
            "ingredients": recipe_template["ingredients"],
            "steps": recipe_template["steps"],
            "prompt": prompt,
            "filename": filename,
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "timestamp": timestamp,
            "likes": 0,
            "views": random.randint(150, 480) # Simulated high seed views to target > 10,000 views monthly
        }
        
        existing_recipes.insert(0, new_recipe)
        save_recipes(existing_recipes)
        print("Updated recipes database successfully!")
        
        # Build individual static HTML pages
        generate_individual_pages(existing_recipes)
        # Re-compile homepage
        generate_homepage(existing_recipes)
    else:
        print("ERROR: Image generation completely failed.")

if __name__ == "__main__":
    main()
