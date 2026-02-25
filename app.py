import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# 配置 Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# 飞书配置
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

def get_feishu_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    res = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    return res.json().get("tenant_access_token")

def send_message(open_id, text):
    token = get_feishu_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # 飞书验证
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    # 处理消息
    event = data.get("event", {})
    message = event.get("message", {})
    sender = event.get("sender", {})

    if message.get("message_type") == "text":
        content = json.loads(message.get("content", "{}"))
        user_text = content.get("text", "").strip()
        open_id = sender.get("sender_id", {}).get("open_id")

        # 调用 Gemini
        try:
            response = model.generate_content(user_text)
            reply = response.text
        except Exception as e:
            reply = f"出错了：{str(e)}"

        send_message(open_id, reply)

    return jsonify({"code": 0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

---

**文件二：`requirements.txt`**
```
flask
requests
google-generativeai
