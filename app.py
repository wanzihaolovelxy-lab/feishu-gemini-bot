import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

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
            response = model.generate_content(user_text)
            reply = response.text
        except Exception as e:
            reply = f"出错了：{str(e)}"

        send_message(open_id, reply)

    return jsonify({"code": 0})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

**4.** 拉到页面最下面，点绿色按钮 **「Commit changes」**，在弹出窗口里再点一次 **「Commit changes」**

---

### 2.4 创建第二个文件 `requirements.txt`

**1.** 回到仓库主页，再次点 **「Add file」→「Create new file」**

**2.** 文件名填：
```
requirements.txt
```

**3.** 内容填：
```
flask
requests
google-generativeai
gunicorn
```

**4.** 拉到最下面点 **「Commit changes」→「Commit changes」**

---

# 第三步：部署到 Render（免费服务器）

### 3.1 注册 Render

**1.** 打开 [render.com](https://render.com)

**2.** 点右上角 **「Get Started」**

**3.** 选 **「GitHub」** 方式登录（这样它能直接读取你的代码）

**4.** 授权 GitHub 登录，进入 Render 控制台

---

### 3.2 创建 Web 服务

**1.** 点击页面中央或右上角的 **「New +」**

**2.** 选择 **「Web Service」**

**3.** 在列表里找到 `feishu-gemini-bot`，点右边的 **「Connect」**

**4.** 进入配置页面，按以下填写：

| 字段 | 填写内容 |
|------|---------|
| Name | `feishu-gemini-bot`（随便） |
| Region | Singapore（离国内近） |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |

**5.** 下面选择套餐，选 **「Free」**（免费那个）

---

### 3.3 填写环境变量

在同一页面继续往下滚，找到 **「Environment Variables」** 区域

点 **「Add Environment Variable」**，依次添加 3 个变量（现在先填 1 个，另外 2 个等下一步拿到飞书的信息再来填）：

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | 第一步复制的那串 Key |

**6.** 全部填好后，点最下面的 **「Create Web Service」**

**7.** 等待 2-3 分钟部署，看到绿色 **「Live」** 字样表示成功！

**8.** 记下你的服务地址，在页面顶部，类似：
```
https://feishu-gemini-bot-xxxx.onrender.com
```
**复制保存好这个地址！**

---

# 第四步：飞书开发者后台配置

### 4.1 创建飞书应用

**1.** 打开 [open.feishu.cn/app](https://open.feishu.cn/app)

**2.** 用你的飞书账号登录

**3.** 点击 **「创建企业自建应用」**

**4.** 填写：
- 应用名称：随便填，比如 `Gemini助手`
- 应用描述：随便填
- 点 **「创建」**

---

### 4.2 获取 App ID 和 App Secret

**1.** 进入刚创建的应用

**2.** 左边菜单点 **「凭证与基础信息」**

**3.** 能看到 **App ID** 和 **App Secret**，分别复制

**4.** 回到 Render，点你的服务 → **「Environment」** → 添加剩余 2 个变量：

| Key | Value |
|-----|-------|
| `FEISHU_APP_ID` | 刚复制的 App ID |
| `FEISHU_APP_SECRET` | 刚复制的 App Secret |

填完后 Render 会自动重新部署，等变绿色就好。

---

### 4.3 开通权限

**1.** 回到飞书应用，左边菜单点 **「权限管理」**

**2.** 搜索并开通以下 2 个权限：
- `im:message`（读取消息）
- `im:message:send_as_bot`（发送消息）

---

### 4.4 配置事件订阅

**1.** 左边菜单点 **「事件订阅」**

**2.** 在 **「请求地址配置」** 里填入你的 Render 地址：
```
https://你的地址.onrender.com/webhook
