import os
import re
import json
import glob
import datetime
from google import genai

# 1. Initialize API client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Priority model list
CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

# 3. Load historical records to prevent duplicate topics
HISTORY_FILE = "history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

past_topics_str = ", ".join(history[-60:]) if history else "None"

# 4. Prompt: High-demand, mass-audience consumer web utility
prompt = f"""
Identify a high-demand, practical, client-side web utility tool used by EVERYDAY PEOPLE (students, office workers, social media creators, general consumers). 

DO NOT generate developer-only, coding, or CSS tools (e.g. NO regex, NO flexbox, NO CSS generators, NO code compilers).

Target categories for normal everyday people:
- Social media text styling, line breaker for Instagram/Threads, hashtag counter.
- Student & writing helpers: word/character counter with reading time estimation, sentence case converters, duplicate line remover, text cleaner.
- Finance & everyday calculators: tip & split bill calculator, discount/tax calculator, mortgage/loan monthly payment estimator, savings goal tracker.
- Lifestyle & productivity: sleep cycle calculator (optimal wake-up times), Pomodoro timer, simple habit streak counter, random choice/name picker wheel.

[Previously Created Tools - DO NOT DUPLICATE]:
[{past_topics_str}]

Requirements:
1. Avoid any topic from the list above. Choose a tool that ANY normal user finds immediately useful.
2. First line must strictly be formatted as: TOPIC_NAME: <Short Tool Name in English>
3. Followed by a complete, production-ready, single-file HTML5 document containing modern CSS and vanilla JavaScript.
4. UI & Tech Specs:
   - Beautiful, sleek modern design (clean typography, intuitive controls, instant calculation/preview, one-click copy button).
   - 100% client-side logic (runs in browser, fast, privacy-friendly).
   - Clear input labels and instructions suitable for non-technical users.
   - Insert a clean support note at the bottom:
     '<div style="text-align:center;margin-top:24px;font-size:12px;color:#888;">Free tool. Support via <a href="https://paypal.me/your_paypal_username" target="_blank" style="color:#38bdf8;">PayPal</a></div>'
5. Wrap the entire HTML code inside ```html ... ``` code block. Do not provide conversational filler.
"""

# 5. Call API with fallback support
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
        print(f"Successfully generated using model: {chosen_model}")
        break
    except Exception as e:
        print(f"Model {model_name} failed: {e}. Trying next...")
        continue

if not content:
    try:
        for m in client.models.list():
            if "generateContent" in (getattr(m, "supported_generation_methods", []) or []):
                fallback_name = m.name.split("/")[-1]
                try:
                    res = client.models.generate_content(model=fallback_name, contents=prompt)
                    content = res.text
                    break
                except Exception:
                    continue
    except Exception as err:
        print(f"Fallback list failed: {err}")

if not content:
    raise RuntimeError("All models failed. Please verify API key status.")

# 6. Extract topic name and record to history
topic_match = re.search(r"TOPIC_NAME:\s*(.+)", content)
topic_name = topic_match.group(1).strip() if topic_match else f"Tool_{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
history.append(topic_name)

with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# 7. Extract HTML and save tool
html_match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
html_code = html_match.group(1) if html_match else content

os.makedirs("tools", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', topic_name.lower())[:30]
filename = f"tools/{safe_slug}_{timestamp}.html"

with open(filename, "w", encoding="utf-8") as f:
    f.write(html_code)

print(f"Saved new tool: {filename}")

# 8. Auto-generate modern index.html (Catalog Hub)
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
  <title>Auto Tools Hub - Everyday Free Online Utilities</title>
  <meta name="description" content="A growing collection of free, useful daily tools for productivity, social media, studying, and finance.">
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
      <p class="subtitle">Fast, free, and practical daily tools for everyone.</p>
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
