import os
import re
import json
import datetime
import google.generativeai as genai

# 1. 初始化 API
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 啟用 Google Search 實時檢索工具（讓 AI 直接聯網 Google 查熱門搜尋與痛點）
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[{"google_search": {}}]
)

# 2. 讀取歷史生成記錄（確保絕不重複）
HISTORY_FILE = "history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

past_topics_str = ", ".join(history[-60:]) if history else "None"

# 3. 提示詞：強制使用 Google 搜尋當前熱門工具關鍵字
prompt = f"""
請透過 Google 搜尋了解目前全球搜尋量高、被廣泛需要但又常被抱怨廣告太多或付費牆擋住的「純前端實用微工具（Web Micro Tools / Utilities）」相關關鍵字與趨勢。

【已做過的歷史工具清單（絕對不可重複，名稱或功能雷同均不行！）】：
[{past_topics_str}]

任務要求：
1. 嚴格避開上述歷史清單，挑選一個目前在 Google 上搜尋意圖強烈、解決具體麻煩痛點的單頁純前端工具（例如：字元精確統計與特定平台限制檢查、正則表達式視覺化與測試、CSS/SVG代碼生成、特定時區/時間戳轉換、純前端檔案雜湊比對等）。
2. 第一行請固定輸出：TOPIC_NAME: <工具簡短名稱（英文）>
3. 緊接著輸出完整的單一 HTML5 檔案代碼（包含現代深色質感的 CSS 與原生 JavaScript）。
4. 網頁要求：
   - 現代簡潔 UI、深色背景、圓角卡片設計、清晰的輸入/輸出區、一鍵複製按鈕。
   - 所有邏輯純瀏覽器端（Client-side）運作，不依賴後端伺服器。
   - 底部加上一行贊助標籤：
     '<div style="text-align:center;margin-top:24px;font-size:12px;color:#888;">Free tool. Support via <a href="https://paypal.me/你的PayPal帳號" target="_blank" style="color:#38bdf8;">PayPal</a></div>'
5. 網頁代碼請用 ```html 包裹，不要輸出多餘說明。
"""

response = model.generate_content(prompt)
content = response.text

# 4. 解析工具名稱並記錄歷史（確保下次不重複）
topic_match = re.search(r"TOPIC_NAME:\s*(.+)", content)
topic_name = topic_match.group(1).strip() if topic_match else f"Tool_{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
history.append(topic_name)

with open(HISTORY_FILE, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# 5. 提取 HTML 並存檔
html_match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
html_code = html_match.group(1) if html_match else content

os.makedirs("tools", exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', topic_name.lower())[:30]
filename = f"tools/{safe_slug}_{timestamp}.html"

with open(filename, "w", encoding="utf-8") as f:
    f.write(html_code)

print(f"成功透過 Google 趨勢生成全新工具（無重複）：{topic_name} -> {filename}")
