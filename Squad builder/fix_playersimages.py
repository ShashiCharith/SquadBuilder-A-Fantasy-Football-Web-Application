import os
import sqlite3
import requests

DB_PATH = "players.db"   # make sure the name matches your DB file

# 1️⃣ Create local folder for images
os.makedirs("static/images/players", exist_ok=True)

# 2️⃣ Connect to database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, image_url FROM players")
rows = cur.fetchall()

# 3️⃣ Loop through all players
for player_id, url in rows:
    if url and "cdn.sofifa.net" in url:
        filename = f"static/images/players/{player_id}.png"
        print(f"Downloading image for player {player_id}...")

        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(resp.content)
                # Update DB to point to local path
                new_path = f"/static/images/players/{player_id}.png"
                cur.execute("UPDATE players SET image_url=? WHERE id=?", (new_path, player_id))
            else:
                print(f"⚠️ Failed to fetch image {url} (status {resp.status_code})")

        except Exception as e:
            print(f"❌ Error for player {player_id}: {e}")

conn.commit()
conn.close()
print("✅ Done! All Sofifa images downloaded locally.")
