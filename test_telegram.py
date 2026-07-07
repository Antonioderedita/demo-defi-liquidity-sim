import requests

TELEGRAM_BOT_TOKEN = "8779936791:AAEWTCCxDOyVqK05eXGc07_yMdz0QJfGvfY"
TELEGRAM_CHAT_ID = "5955452088"

print("Invio ping a Telegram...")
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": "✅ Test di connessione dal terminale del Mac."
}

risposta = requests.post(url, json=payload)
print(f"Risposta del server Telegram: {risposta.json()}")