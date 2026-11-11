import os
import re
import json
import glob
import datetime
from google import genai

# 1. 初始化 API Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 優先採用的模型清單
CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

# 2. 獲取使用者在 GitHub Actions 輸入的主題
user_topic = os.environ.get("CUSTOM_TOPIC", "").strip()
if not user_topic:
    user_topic = "Everyday Practical Utility"

print(f"Target Tool Topic: {user_topic}")

# 3. 讀取歷史清單以防重複記錄
HISTORY_FILE = "history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

# 4. 針對指定主題撰寫嚴格 Prompt（無外連贊助、純前端完整功能）
prompt = f"""
Build a complete, standalone, production-ready single-file HTML5 utility web app for the following topic:
Topic: {user_topic}

Requirements:
1. First line must strictly be formatted as: TOPIC_NAME: {user_topic}
2. Followed by a complete, functional, single-file HTML5 document containing modern CSS and vanilla JavaScript.
3. Design & Functional Specs:
   - Modern, sleek dark-themed UI (deep dark background #0f172a, clean cards #1e293b, crisp typography, intuitive interactive buttons and inputs).
   - 100% functional client-side logic using vanilla JavaScript (instant calculations, inputs validation, interactive dashboard or preview).
   - Practical, polished user experience suited for ordinary people (students, consumers, everyday users).
   - DO NOT include any donation, PayPal, BuyMeACoffee, or external sponsor links.
4. Wrap the entire HTML code inside ```html ... ``` code block. Do not provide conversational filler.
"""

# 5. 呼叫 Gemini API
content = None
chosen_model = None

for model_name in CANDIDATE_MODELS:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        content = response.text
        chosen_model = model_name
        print(f"Successfully generated using: {chosen_model}")
        break
    except Exception as e:
        print(f"Model {model_name} failed: {e}. Trying next candidate...")
        continue

if not content:
    try:
        for m in client.models.list():
            if "generateContent" in (getattr(m, "supported_generation_methods", []) or []):
                fallback_name = m.name.split("/")[-1]
                try:
                    res = client.models.generate_content(model=fallback_name, contents=prompt)
                    content = res.text
                    chosen_model = fallback_name
                    print(f"Successfully generated using fallback: {chosen_model}")
                    break
                except Exception:
                    continue
    except Exception as err:
        print(f"Fallback list failed: {err}")

if not content:
    raise RuntimeError("All models failed. Please verify API key status.")

# 6. 記錄主題至歷史檔
history.append(user_topic)
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# 7. 提取 HTML 並存入 tools/ 資料夾
html_match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
html_code = html_match.group(1) if html_match else content

os.makedirs("tools", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', user_topic.lower())[:30]
filename = f"tools/{safe_slug}_{timestamp}.html"

with open(filename, "w", encoding="utf-8") as f:
    f.write(html_code)

print(f"Tool created successfully: {filename}")

# 8. 自動更新首頁 index.html 目錄
all_tools = sorted(glob.glob("tools/*.html"), reverse=True)
tool_links_html = ""
for t_path in all_tools:
    rel_url = t_path.replace("\\", "/")
    display_title = os.path.basename(t_path).replace(".html", "").replace("_", " ").title()
    tool_links_html += f"""
      <a href="/{rel_url}" class="card">
        <h3>{display_title}</h3>
        <p>Free, instant, client-side browser utility.</p>
        <span class="badge">Open Tool &rarr;</span>
      </a>
    """

index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auto Tools Hub - Useful Daily Utilities</title>
  <meta name="description" content="A curated collection of practical everyday web tools for productivity, finance, and daily life.">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; min-height: 100vh; padding: 40px 20px; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    header {{ text-align: center; margin-bottom: 40px; }}
    h1 {{ font-size: 2.4rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }}
    p.subtitle {{ color: #94a3b8; font-size: 1.1rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-decoration: none; color: inherit; transition: all 0.2s ease; display: flex; flex-direction: column; justify-content: space-between; }}
    .card:hover {{ border-color: #38bdf8; transform: translateY(-3px); box-shadow: 0 10px 20px -10px rgba(56, 189, 248, 0.3); }}
    .card h3 {{ font-size: 1.1rem; color: #f1f5f9; margin-bottom: 8px; }}
    .card p {{ font-size: 0.85rem; color: #94a3b8; line-height: 1.4; margin-bottom: 16px; }}
    .badge {{ font-size: 0.8rem; font-weight: 600; color: #38bdf8; align-self: flex-start; }}
    footer {{ text-align: center; margin-top: 50px; font-size: 0.85rem; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Auto Tools Hub</h1>
      <p class="subtitle">Practical and intuitive daily utilities for everyone.</p>
    </header>
    <div class="grid">
      {tool_links_html}
    </div>
    <footer>
      &copy; {datetime.datetime.now().year} Auto Tools Hub. Practical utilities for daily life.
    </footer>
  </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html_content)

print("Catalog index.html successfully updated!")
