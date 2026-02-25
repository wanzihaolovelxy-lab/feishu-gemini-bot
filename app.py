import os
import json
import requests
from openai import OpenAI
from flask import Flask, request, jsonify

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("MINIMAX_API_KEY"),
    base_url="https://api.minimaxi.chat/v1"
)

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
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    event = data.get("event", {})
    message = event.get("message", {})
    sender = event.get("sender", {})

    if message.get("message_type") == "text":
        content = json.loads(message.get("content", "{}"))
        user_text = content.get("text", "").strip()
        open_id = sender.get("sender_id", {}).get("open_id")

        try:
            response = client.chat.completions.create(
                model="MiniMax-Text-01",
                messages=[{"role": "user", "content": user_text}]
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"出错了：{str(e)}"

        send_message(open_id, reply)

    return jsonify({"code": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

**4.** 再点 `requirements.txt` 编辑，内容改成：
```
flask
requests
openai
gunicorn
