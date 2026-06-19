"""
Chuyển User Access Token ngắn hạn → Long-lived Token 60 ngày.
Chạy: python extend_token.py
Điền META_APP_SECRET vào .env trước khi chạy.
"""
import os, requests
from dotenv import load_dotenv
load_dotenv('.env')

APP_ID     = os.environ.get("META_APP_ID", "2500156147069438")
APP_SECRET = os.environ.get("META_APP_SECRET", "")
TOKEN      = os.environ.get("META_ACCESS_TOKEN", "")

if not APP_SECRET:
    print("Chua co APP_SECRET trong .env!")
    print("-> Vao developers.facebook.com/apps/2500156147069438/settings/basic")
    print("-> Click 'Hien' canh App Secret -> copy -> them vao .env")
    exit(1)

r = requests.get("https://graph.facebook.com/v20.0/oauth/access_token", params={
    "grant_type": "fb_exchange_token",
    "client_id": APP_ID,
    "client_secret": APP_SECRET,
    "fb_exchange_token": TOKEN
})
data = r.json()
if "access_token" in data:
    new_token = data["access_token"]
    expires   = data.get("expires_in", "unknown")
    print(f"Token moi (het han sau {int(expires)//86400} ngay):")
    print(new_token)

    # Tu dong cap nhat .env
    env_path = ".env"
    with open(env_path, "r") as f:
        content = f.read()
    old_line = [l for l in content.splitlines() if l.startswith("META_ACCESS_TOKEN=")]
    if old_line:
        content = content.replace(old_line[0], f"META_ACCESS_TOKEN={new_token}")
        with open(env_path, "w") as f:
            f.write(content)
        print(".env da duoc cap nhat tu dong!")
    print("\nCopy token nay len Railway Variables -> META_ACCESS_TOKEN")
else:
    print("Loi:", data)
