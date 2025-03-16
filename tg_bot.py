import requests
import time
import json
from flask import Flask, request

# ✅ Correct Telegram Bot Token (Make sure this is a string!)
TELEGRAM_BOT_TOKEN = "7728554236:AAFFmvsEyHCudk6C1_uMqN5CHAFWfF0UrH8"
TELEGRAM_CHAT_ID = "5462964617"  # ✅ Your Chat ID

# ✅ API endpoint for fetching crypto data
API_URL = "https://coinselection.fun/appApi/fetch_coin_bybit.php?timeframe=15m"

# ✅ Flask app for handling Telegram webhook
app = Flask(__name__)

def fetch_coin_data():
    """Fetches crypto data from the website API."""
    try:
        response = requests.get(API_URL)
        data = response.json()  # Convert response to JSON
        
        # Extract the coin categories
        parsed_data = json.loads(data[0]["coin_data"])
        spot_winners = parsed_data["spot"]["top_15_high"]
        spot_losers = parsed_data["spot"]["top_15_low"]
        futures_winners = parsed_data["futures"]["top_15_high"]
        futures_losers = parsed_data["futures"]["top_15_low"]
        
        return spot_winners, spot_losers, futures_winners, futures_losers
    except Exception as e:
        return f"Error fetching data: {str(e)}"

def format_coin_list(title, coins):
    """Formats the coin list with arrows for price movement and better readability."""
    if not coins:
        return f"*{title}* 🔥\nNo data available.\n\n"

    message = f"*{title}* 🔥\n\n"

    for coin in coins:
        last_price = f"{float(coin['Last Price']):,.6f}"  # 6 decimal places
        change_percent = float(coin['Change (%)'])
        high_price = f"{float(coin['High']):,.4f}"  # 4 decimal places
        low_price = f"{float(coin['Low']):,.4f}"  # 4 decimal places
        
        # ✅ Add Green ⬆️ for increasing prices, Red ⬇️ for decreasing prices
        arrow = "🟢 ⬆️" if change_percent > 0 else "🔴 ⬇️"
        
        message += f"🔹 *{coin['Pair']}*\n"
        message += f"   💰 *Last Price:* `{last_price}`\n"
        message += f"   {arrow} *Change:* `{change_percent:.2f}%`\n"
        message += f"   🔺 *High:* `{high_price}`\n"
        message += f"   🔻 *Low:* `{low_price}`\n\n"  # Double spacing added
    
    return message

def send_to_telegram(message):
    """Sends the formatted message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    """Handles Telegram bot commands."""
    data = request.get_json()

    if "message" in data:
        chat_id = str(data["message"]["chat"]["id"])  # Convert to string
        text = data["message"]["text"]

        if text.lower() == "/refresh":
            send_to_telegram("🔄 Manually refreshing crypto data...")

            spot_winners, spot_losers, futures_winners, futures_losers = fetch_coin_data()
            spot_message = format_coin_list("🔥 Spot Top Movers", spot_winners) + format_coin_list("🔥 Spot Top Losers", spot_losers)
            futures_message = format_coin_list("🔥 Futures Top Movers", futures_winners) + format_coin_list("🔥 Futures Top Losers", futures_losers)

            send_to_telegram(spot_message)
            send_to_telegram(futures_message)

    return "OK", 200

def main():
    """Fetches data every 1 minute, sends alert every 15 minutes."""
    counter = 0  # ✅ Counter to track 15-minute intervals

    while True:
        data = fetch_coin_data()

        if isinstance(data, str) and "Error" in data:
            print("⚠ Error fetching crypto data!")
        else:
            spot_winners, spot_losers, futures_winners, futures_losers = data
            
            # ✅ Refresh data every 1 minute (but send message every 15 mins)
            if counter % 15 == 0:  # Every 15th loop (15 minutes)
                spot_message = format_coin_list("🔥 Spot Top Movers", spot_winners) + format_coin_list("🔥 Spot Top Losers", spot_losers)
                futures_message = format_coin_list("🔥 Futures Top Movers", futures_winners) + format_coin_list("🔥 Futures Top Losers", futures_losers)

                send_to_telegram(spot_message)
                send_to_telegram(futures_message)
                print("✅ Spot & Futures Messages Sent to Telegram!")

        time.sleep(60)  # ✅ Refresh data every 1 minute
        counter += 1  # ✅ Increase counter

if __name__ == "__main__":
    from threading import Thread
    thread = Thread(target=main)
    thread.start()
    app.run(host="0.0.0.0", port=5000)
