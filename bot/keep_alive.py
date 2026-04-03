from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot activo 🟢"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

print("🔗 URL pública del Repl:", os.environ.get("REPLIT_URL") or os.environ.get("REPLIT_DEV_DOMAIN"))
