import os
import re
import json
import datetime
from google import genai

# 1. Initialize API client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. Priority model list as requested
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

# 4. Prompt: High-demand, low-competition client-side utility
prompt = f"""
Identify a high-demand, practical, client-side web utility tool based on common global developer and productivity search trends (e.g. text manipulation, format converters, calculators, format validators, CSS generators).

[Previously Created Tools - DO NOT DUPLICATE]:
[{past_topics_str}]

Requirements:
1. Avoid any topic from the list above. Choose a highly practical, standalone, client-side web utility.
2. First line must strictly be formatted as: TOPIC_NAME: <Short Tool Name in English>
3. Followed by a complete, production-ready, single-file HTML5 document containing modern CSS and vanilla JavaScript.
4. UI & Tech Specs:
   - Modern, sleek dark-themed UI (clean typography, rounded cards, input/output sections, copy-to-clipboard button).
   - 100% client-side (no backend or external API keys required).
   - Valid HTML, modern CSS, and robust error-free JavaScript.
   - Include standard SEO tags (title, meta description) matching the target utility keyword.
   - Insert a clean support note at the bottom:
     '<div style="text-align:center;margin-top:24px;font-size:12px;color:#888;">Free tool. Support via <a href="https://paypal.me/your_paypal_username" target="_blank" style="color:#38bdf8;">PayPal</a></div>'
5. Wrap the entire HTML code inside ```html ... ``` code block. Do not provide conversational filler.
"""

# 5. Call API with fallback support
content = None
chosen_model = None

# First attempt: Try the specific requested models
for model_name in CANDIDATE_MODELS:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        content = response.text
        chosen_model = model_name
        print(f"Successfully generated using specified model: {chosen_model}")
        break
    except Exception as e:
        print(f"Model {model_name} not available: {e}. Trying next...")
        continue

# Fallback: If requested names differ slightly, auto-query available models from account
if not content:
    print("Querying account for available models supporting generateContent...")
    try:
        for m in client.models.list():
            if "generateContent" in (getattr(m, "supported_generation_methods", []) or []):
                fallback_name = m.name.split("/")[-1]
                try:
                    response = client.models.generate_content(
                        model=fallback_name,
                        contents=prompt
                    )
                    content = response.text
                    chosen_model = fallback_name
                    print(f"Successfully generated using fallback model: {chosen_model}")
                    break
                except Exception:
                    continue
    except Exception as list_err:
        print(f"Could not list models: {list_err}")

if not content:
    raise RuntimeError("All models failed. Please check API key status and permissions.")

# 6. Extract topic name and record to history
topic_match = re.search(r"TOPIC_NAME:\s*(.+)", content)
topic_name = topic_match.group(1).strip() if topic_match else f"Tool_{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
history.append(topic_name)

with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# 7. Extract HTML and save file
html_match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
html_code = html_match.group(1) if html_match else content

os.makedirs("tools", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', topic_name.lower())[:30]
filename = f"tools/{safe_slug}_{timestamp}.html"

with open(filename, "w", encoding="utf-8") as f:
    f.write(html_code)

print(f"Tool generation complete: {topic_name} -> {filename}")
