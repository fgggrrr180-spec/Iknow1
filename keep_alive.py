# keep_alive.py
from flask import Flask
from threading import Thread

# Flask application (web server) start kar rahe hain
app = Flask('')

# Root URL (/) par jaane par yeh function chalta hai
@app.route('/')
def home():
    return "Mahiru Bot is alive and running 24/7!"

# Web server ko background thread mein chalao
def run():
  # 0.0.0.0 aur 8080 port Replit ke liye standard hain
  app.run(host='0.0.0.0', port=8080)

# Main function jo background thread ko start karegi
def keep_alive():
    t = Thread(target=run)
    t.start()