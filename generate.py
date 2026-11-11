import os
import re
import json
import urllib.request
import datetime
import google.generativeai as genai

# 1. 初始化 API
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# 2. 讀取歷史生成記錄（確保絕不重複）
HISTORY_FILE = "history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

past_topics_str = ", ".join(history[-50:]) if history else "None"

# 3. 自動連網抓取當前熱門靈感（Reddit r/InternetIsBeautiful & r/webdev）
trending_context = ""
try:
    req = urllib.request.Request(
        "https://www.reddit.com/r/InternetIsBeautiful/hot.json?limit=10",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        titles = [post["data"]["title"] for post in data["data"]["children"]]
        trending_context = "當前網上熱門工具趨勢參考：\n" + "\n".join(titles)
except Exception as e:
    trending_context = "以目前全球高搜尋量、高點擊的開發者與效率微工具為主。"

# 4. 要求 AI 避開歷史、結合爆款趨勢設計工具
prompt = f"""
你是一個專做高流量、高實用性 Web 微工具的產品經理與前端工程師。

【當前趨勢與背景】：
{trending_context}

【已做過的歷史工具（絕對不可重複！）】：
[{past_topics_str}]

任務要求：
1. 嚴格避開上述已做過的工具，挑選一個目前需求極高、解決具體繁瑣痛點的單頁純前端工具（例如：進階 Markdown 格式轉換、正則可視化、特定社群文本排版、音訊/圖片瀏覽器本地處理、特定法規/稅務試算等）。
2. 第一行請固定輸出：TOPIC_NAME: <工具簡短名稱（英文）>
3. 緊接著輸出完整的單一 HTML5 檔案（包含現代深色質感的 CSS 與原生 JavaScript）。
4. 介面要求：
   - 現代簡潔 UI、圓角卡片、清晰的輸入/輸出區、一鍵複製按鈕。
   - 純瀏覽器端（Client-side）運作，不依賴任何後端伺服器。
   - 底部加入贊助提示：
     '<div style="text-align:center;margin-top:24px;font-size:12px;color:#888;">Free tool. Support via <a href="https://paypal.me/你的PayPal帳號" target="_blank" style="color:#38bdf8;">PayPal</a></div>'
5. 代碼請用 ```html 包裹。
"""

response = model.generate_content(prompt)
content = response.text

# 5. 解析工具名稱並記錄歷史
topic_match = re.search(r"TOPIC_NAME:\s*(.+)", content)
topic_name = topic_match.group(1).strip() if topic_match else f"Tool_{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
history.append(topic_name)
with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# 6. 提取 HTML 並存檔
html_match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
html_code = html_match.group(1) if html_match else content

os.makedirs("tools", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', topic_name.lower())[:30]
filename = f"tools/{safe_slug}_{timestamp}.html"

with open(filename, "w", encoding="utf-8") as f:
    f.write(html_code)

print(f"成功生成全新工具（無重複）：{topic_name} -> {filename}")
