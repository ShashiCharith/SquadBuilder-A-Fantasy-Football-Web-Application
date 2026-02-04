import requests
import sqlite3
import time

# === CONFIG ===
API_KEY = "1f9d850cb28ae49a7ef4216e475f0058"
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY
}

# === DATABASE SETUP ===
conn = sqlite3.connect("players.db")
cursor = conn.cursor()

def create_players_table():
    """Creates the players table with a new 'cost' column."""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        position TEXT NOT NULL,
        club TEXT NOT NULL,
        league_id INTEGER NOT NULL,
        nationality TEXT,
        image_url TEXT,
        cost INTEGER NOT NULL -- ADDED: This column will store the fantasy cost
    );
    """)
    conn.commit()

# === HELPER FUNCTION ===
def calculate_cost(rating_str, position):
    """
    Calculates a fantasy cost based on a player's rating string (e.g., "7.5") and position.
    """
    # Default cost for players with no rating data
    if rating_str is None:
        return 40

    try:
        rating = float(rating_str)
        # Scale rating (typically 6-9) to a fantasy cost (typically 40-100)
        base_cost = int((rating - 5.5) * 25 + 40)
    except (ValueError, TypeError):
        return 40  # Return default if rating is not a valid number

    # Apply positional multipliers (attackers are more valuable in fantasy)
    if position == 'Attacker':
        cost = int(base_cost * 1.15)  # 15% markup
    elif position == 'Midfielder':
        cost = int(base_cost * 1.05)  # 5% markup
    else:  # Defender or Goalkeeper
        cost = base_cost

    # Ensure a minimum cost of 40 and a max of 150
    return max(40, min(cost, 150))


# === FETCHING FROM API ===
def get_players(league_id, season=2023):
    """Fetches players from the API, calculates their cost, and inserts them."""
    url = f"{BASE_URL}/players"
    querystring = {"league": str(league_id), "season": str(season), "page": 1}

    while True:
        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            response.raise_for_status() # Raise an exception for bad status codes (like 404, 500)
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request failed: {e}")
            break

        if not data.get("response") or not data["response"]:
            print(f"Error or no data in API response for league {league_id}, page {querystring['page']}")
            print(data.get("errors", "No error details provided."))
            break

        for item in data["response"]:
            # Skip if player statistics are missing, as we need them for rating and position
            if not item.get("statistics") or not item["statistics"][0]:
                continue

            player = item["player"]
            stats = item["statistics"][0]
            position = stats["games"]["position"]
            rating = stats["games"]["rating"]

            # Use the helper function to generate a cost
            cost = calculate_cost(rating, position)

            cursor.execute("""
                INSERT OR IGNORE INTO players (name, position, club, league_id, nationality, image_url, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                player["name"],
                position if position else "Unknown",
                stats["team"]["name"],
                league_id,
                player["nationality"],
                player["photo"],
                cost  # Insert the calculated cost
            ))

        conn.commit()

        # Handle pagination
        current_page = data["paging"]["current"]
        total_pages = data["paging"]["total"]
        if current_page < total_pages:
            querystring["page"] += 1
            print(f"Fetching page {querystring['page']}/{total_pages} for league {league_id}...")
            time.sleep(2)  # Be polite to the API
        else:
            break
    print(f"Finished fetching for league {league_id}.")


# === FETCH KEY LEAGUES ===
def update_selected_leagues():
    leagues = [39, 140]  # EPL, La Liga
    for league in leagues:
        print(f"⚽ Fetching players for league {league}...")
        get_players(league, season=2023) # Using 2023 season for current data
    print("✅ Key European leagues inserted into database!")


# === MANUAL EXTRA PLAYERS ===
def insert_extra_players():
    """
    Inserts a curated list of top 100 world footballers with assigned costs.
    """
    # Data format: (Name, Position, Club, League ID, Nationality, Image URL, Cost)
    # Cost is an integer representing millions (e.g., 130 = 13.0m)
    extras = [
    # GOALKEEPERS
    ("Thibaut Courtois", "Goalkeeper", "Real Madrid", 140, "Belgium", "https://cdn.sofifa.net/players/192/119/24_120.png", 60),
    ("Alisson Becker", "Goalkeeper", "Liverpool", 39, "Brazil", "https://cdn.sofifa.net/players/212/831/24_120.png", 60),
    ("Ederson", "Goalkeeper", "Manchester City", 39, "Brazil", "https://cdn.sofifa.net/players/210/257/24_120.png", 55),
    ("Marc-André ter Stegen", "Goalkeeper", "Barcelona", 140, "Germany", "https://cdn.sofifa.net/players/192/448/24_120.png", 55),
    ("Jan Oblak", "Goalkeeper", "Atlético Madrid", 140, "Slovenia", "https://cdn.sofifa.net/players/200/389/24_120.png", 50),
    ("Manuel Neuer", "Goalkeeper", "Bayern Munich", 78, "Germany", "https://cdn.sofifa.net/players/167/495/24_120.png", 45),
    ("Mike Maignan", "Goalkeeper", "AC Milan", 135, "France", "https://cdn.sofifa.net/players/215/698/26_120.png", 50),
    ("Gianluigi Donnarumma", "Goalkeeper", "Paris Saint-Germain", 61, "Italy", "https://cdn.sofifa.net/players/230/621/24_120.png", 50),
    ("Yassine Bounou", "Goalkeeper", "Al Hilal", 307, "Morocco", "https://cdn.sofifa.net/players/209/981/24_120.png", 45),
    ("André Onana", "Goalkeeper", "Manchester United", 39, "Cameroon", "https://cdn.sofifa.net/players/226/753/24_120.png", 50),
    ("David De Gea", "Goalkeeper", "Fiorentina", 135, "Spain", "https://cdn.sofifa.net/players/193/080/24_120.png", 50),
    ("Emiliano Martínez", "Goalkeeper", "Aston Villa", 39, "Argentina", "https://cdn.sofifa.net/players/202/811/24_120.png", 55),

    # DEFENDERS
    ("Virgil van Dijk", "Defender", "Liverpool", 39, "Netherlands", "https://cdn.sofifa.net/players/203/376/24_120.png", 70),
    ("Rúben Dias", "Defender", "Manchester City", 39, "Portugal", "https://cdn.sofifa.net/players/239/818/24_120.png", 70),
    ("Marquinhos", "Defender", "Paris Saint-Germain", 61, "Brazil", "https://cdn.sofifa.net/players/207/865/24_120.png", 65),
    ("William Saliba", "Defender", "Arsenal", 39, "France", "https://cdn.sofifa.net/players/241/636/24_120.png", 65),
    ("Éder Militão", "Defender", "Real Madrid", 140, "Brazil", "https://cdn.sofifa.net/players/240/130/24_120.png", 65),
    ("Joško Gvardiol", "Defender", "Manchester City", 39, "Croatia", "https://cdn.sofifa.net/players/251/517/24_120.png", 60),
    ("Ronald Araújo", "Defender", "Barcelona", 140, "Uruguay", "https://cdn.sofifa.net/players/245/575/24_120.png", 65),
    ("Matthijs de Ligt", "Defender", "Bayern Munich", 78, "Netherlands", "https://cdn.sofifa.net/players/235/243/24_120.png", 60),
    ("David Alaba", "Defender", "Real Madrid", 140, "Austria", "https://cdn.sofifa.net/players/197/445/24_120.png", 55),
    ("Antonio Rüdiger", "Defender", "Real Madrid", 140, "Germany", "https://cdn.sofifa.net/players/205/494/24_120.png", 55),
    ("Kyle Walker", "Defender", "Manchester City", 39, "England", "https://cdn.sofifa.net/players/188/377/24_120.png", 55),
    ("Achraf Hakimi", "Defender", "Paris Saint-Germain", 61, "Morocco", "https://cdn.sofifa.net/players/235/213/24_120.png", 70),
    ("Trent Alexander-Arnold", "Defender", "Liverpool", 39, "England", "https://cdn.sofifa.net/players/231/281/24_120.png", 80),
    ("Andrew Robertson", "Defender", "Liverpool", 39, "Scotland", "https://cdn.sofifa.net/players/216/267/24_120.png", 65),
    ("Theo Hernández", "Defender", "AC Milan", 135, "France", "https://cdn.sofifa.net/players/232/656/24_120.png", 65),
    ("Alphonso Davies", "Defender", "Bayern Munich", 78, "Canada", "https://cdn.sofifa.net/players/234/396/24_120.png", 65),
    ("John Stones", "Defender", "Manchester City", 39, "England", "https://cdn.sofifa.net/players/203/574/24_120.png", 55),
    ("Jules Koundé", "Defender", "Barcelona", 140, "France", "https://cdn.sofifa.net/players/241/486/24_120.png", 55),
    ("Kim Min-jae", "Defender", "Bayern Munich", 78, "South Korea", "https://cdn.sofifa.net/players/251/185/24_120.png", 60),
    ("Lisandro Martínez", "Defender", "Manchester United", 39, "Argentina", "https://cdn.sofifa.net/players/238/721/24_120.png", 55),
    ("Alejandro Balde", "Defender", "FC Barcelona", 140, "Spain", "https://cdn.sofifa.net/players/262/759/24_120.png", 60),
    ("Nuno Mendes", "Defender", "Paris Saint-Germain", 61, "Portugal", "https://cdn.sofifa.net/players/252/511/24_120.png", 60),
    ("Jordi Alba", "Defender", "Inter Miami", 253, "Spain", "https://cdn.sofifa.net/players/189/332/24_120.png", 65),
    ("Sergio Ramos", "Defender", "Sevilla FC", 140, "Spain", "https://cdn.sofifa.net/players/155/862/24_120.png", 60),
    ("Reece James", "Defender", "Chelsea", 39, "England", "https://cdn.sofifa.net/players/234/828/24_120.png", 65),
    ("Dani Carvajal", "Defender", "Real Madrid", 140, "Spain", "https://cdn.sofifa.net/players/204/963/24_120.png", 60),
    ("Harry Maguire", "Defender", "Manchester United", 39, "England", "https://cdn.sofifa.net/players/203/269/24_120.png", 50),
    ("Cristian Romero", "Defender", "Tottenham Hotspur", 39, "Argentina", "https://cdn.sofifa.net/players/234/181/24_120.png", 65),
    ("Thiago Silva", "Defender", "Fluminense", 0, "Brazil", "https://cdn.sofifa.net/players/164/240/24_120.png", 55),

    # MIDFIELDERS
    ("Kevin De Bruyne", "Midfielder", "Manchester City", 39, "Belgium", "https://cdn.sofifa.net/players/192/985/24_120.png", 125),
    ("Rodri", "Midfielder", "Manchester City", 39, "Spain", "https://cdn.sofifa.net/players/231/866/24_120.png", 100),
    ("Jude Bellingham", "Midfielder", "Real Madrid", 140, "England", "https://cdn.sofifa.net/players/252/371/24_120.png", 110),
    ("Martin Ødegaard", "Midfielder", "Arsenal", 39, "Norway", "https://cdn.sofifa.net/players/222/665/24_120.png", 95),
    ("Bernardo Silva", "Midfielder", "Manchester City", 39, "Portugal", "https://cdn.sofifa.net/players/218/667/24_120.png", 90),
    ("Luka Modrić", "Midfielder", "Real Madrid", 140, "Croatia", "https://cdn.sofifa.net/players/177/003/24_120.png", 80),
    ("Frenkie de Jong", "Midfielder", "Barcelona", 140, "Netherlands", "https://cdn.sofifa.net/players/228/702/24_120.png", 85),
    ("Joshua Kimmich", "Midfielder", "Bayern Munich", 78, "Germany", "https://cdn.sofifa.net/players/212/622/24_120.png", 90),
    ("Federico Valverde", "Midfielder", "Real Madrid", 140, "Uruguay", "https://cdn.sofifa.net/players/239/053/24_120.png", 95),
    ("Pedri", "Midfielder", "Barcelona", 140, "Spain", "https://cdn.sofifa.net/players/251/854/24_120.png", 90),
    ("Declan Rice", "Midfielder", "Arsenal", 39, "England", "https://cdn.sofifa.net/players/234/378/24_120.png", 85),
    ("Bruno Fernandes", "Midfielder", "Manchester United", 39, "Portugal", "https://cdn.sofifa.net/players/212/198/24_120.png", 95),
    ("İlkay Gündoğan", "Midfielder", "Barcelona", 140, "Germany", "https://cdn.sofifa.net/players/186/942/24_120.png", 85),
    ("Jamal Musiala", "Midfielder", "Bayern Munich", 78, "Germany", "https://cdn.sofifa.net/players/256/790/24_120.png", 105),
    ("Casemiro", "Midfielder", "Manchester United", 39, "Brazil", "https://cdn.sofifa.net/players/202/262/24_120.png", 80),
    ("Nicolò Barella", "Midfielder", "Inter Milan", 135, "Italy", "https://cdn.sofifa.net/players/222/744/24_120.png", 85),
    ("Toni Kroos", "Midfielder", "Real Madrid", 140, "Germany", "https://cdn.sofifa.net/players/182/521/24_120.png", 80),
    ("Gavi", "Midfielder", "Barcelona", 140, "Spain", "https://cdn.sofifa.net/players/264/240/24_120.png", 85),
    ("Alexis Mac Allister", "Midfielder", "Liverpool", 39, "Argentina", "https://cdn.sofifa.net/players/239/098/24_120.png", 80),
    ("Enzo Fernández", "Midfielder", "Chelsea", 39, "Argentina", "https://cdn.sofifa.net/players/257/628/24_120.png", 80),
    ("Aurélien Tchouaméni", "Midfielder", "Real Madrid", 140, "France", "https://cdn.sofifa.net/players/241/632/24_120.png", 80),
    ("Eduardo Camavinga", "Midfielder", "Real Madrid", 140, "France", "https://cdn.sofifa.net/players/243/725/24_120.png", 85),
    ("Bruno Guimarães", "Midfielder", "Newcastle United", 39, "Brazil", "https://cdn.sofifa.net/players/247/851/24_120.png", 80),
    ("Florian Wirtz", "Midfielder", "Bayer Leverkusen", 78, "Germany", "https://cdn.sofifa.net/players/256/630/24_120.png", 90),
    ("Sandro Tonali", "Midfielder", "Newcastle United", 39, "Italy", "https://cdn.sofifa.net/players/243/381/24_120.png", 75),
    ("Marcelo Brozović", "Midfielder", "Al Nassr", 307, "Croatia", "https://cdn.sofifa.net/players/205/374/24_120.png", 70),
    ("N'Golo Kanté", "Midfielder", "Al Ittihad", 307, "France", "https://cdn.sofifa.net/players/215/914/24_120.png", 75),
    ("Sergio Busquets", "Midfielder", "Inter Miami", 253, "Spain", "https://cdn.sofifa.net/players/189/511/24_120.png", 70),
    ("Xavi Simons", "Midfielder", "RB Leipzig", 78, "Netherlands", "https://cdn.sofifa.net/players/245/367/24_120.png", 85),
    ("James Maddison", "Midfielder", "Tottenham Hotspur", 39, "England", "https://cdn.sofifa.net/players/220/697/24_120.png", 85),
    ("Paul Pogba", "Midfielder", "Juventus", 135, "France", "https://cdn.sofifa.net/players/195/864/24_120.png", 70),
    ("Philippe Coutinho", "Midfielder", "Vasco da Gama", 0, "Brazil", "https://cdn.sofifa.net/players/189/242/24_120.png", 65),
    ("Vitinha", "Midfielder", "Paris Saint-Germain", 61, "Portugal", "https://cdn.sofifa.net/players/242/481/24_120.png", 80),
    ("Mason Mount", "Midfielder", "Manchester United", 39, "England", "https://cdn.sofifa.net/players/236/602/24_120.png", 75),
    ("Dominik Szoboszlai", "Midfielder", "Liverpool", 39, "Hungary", "https://cdn.sofifa.net/players/236/053/24_120.png", 85),
    ("João Neves", "Midfielder", "Paris Saint-Germain", 61, "Portugal", "https://cdn.sofifa.net/players/270/872/24_120.png", 75),
    ("James Rodríguez", "Midfielder", "Free Agent", 0, "Colombia", "https://cdn.sofifa.net/players/198/710/24_120.png", 70),
    # FORWARDS
    ("Erling Haaland", "Forward", "Manchester City", 39, "Norway", "https://cdn.sofifa.net/players/239/085/24_120.png", 140),
    ("Kylian Mbappé", "Forward", "Paris Saint-Germain", 61, "France", "https://cdn.sofifa.net/players/231/747/24_120.png", 135),
    ("Lionel Messi", "Forward", "Inter Miami", 253, "Argentina", "https://cdn.sofifa.net/players/158/023/24_120.png", 125),
    ("Vinícius Júnior", "Forward", "Real Madrid", 140, "Brazil", "https://cdn.sofifa.net/players/238/794/24_120.png", 120),
    ("Mohamed Salah", "Forward", "Liverpool", 39, "Egypt", "https://cdn.sofifa.net/players/209/331/24_120.png", 125),
    ("Harry Kane", "Forward", "Bayern Munich", 78, "England", "https://cdn.sofifa.net/players/202/126/24_120.png", 125),
    ("Robert Lewandowski", "Forward", "Barcelona", 140, "Poland", "https://cdn.sofifa.net/players/188/545/24_120.png", 115),
    ("Victor Osimhen", "Forward", "Napoli", 135, "Nigeria", "https://cdn.sofifa.net/players/238/550/24_120.png", 110),
    ("Bukayo Saka", "Forward", "Arsenal", 39, "England", "https://cdn.sofifa.net/players/246/528/24_120.png", 110),
    ("Karim Benzema", "Forward", "Al Ittihad", 307, "France", "https://cdn.sofifa.net/players/165/153/24_120.png", 105),
    ("Neymar Jr", "Forward", "Al Hilal", 307, "Brazil", "https://cdn.sofifa.net/players/190/871/24_120.png", 100),
    ("Antoine Griezmann", "Forward", "Atlético Madrid", 140, "France", "https://cdn.sofifa.net/players/194/765/24_120.png", 100),
    ("Lautaro Martínez", "Forward", "Inter Milan", 135, "Argentina", "https://cdn.sofifa.net/players/231/478/24_120.png", 105),
    ("Cristiano Ronaldo", "Forward", "Al Nassr", 307, "Portugal", "https://cdn.sofifa.net/players/020/801/24_120.png", 110),
    ("Son Heung-min", "Forward", "Tottenham Hotspur", 39, "South Korea", "https://cdn.sofifa.net/players/200/104/24_120.png", 100),
    ("Khvicha Kvaratskhelia", "Forward", "Napoli", 135, "Georgia", "https://cdn.sofifa.net/players/247/635/24_120.png", 95),
    ("Rafael Leão", "Forward", "AC Milan", 135, "Portugal", "https://cdn.sofifa.net/players/241/721/24_120.png", 100),
    ("Jack Grealish", "Forward", "Manchester City", 39, "England", "https://cdn.sofifa.net/players/209/231/24_120.png", 85),
    ("Gabriel Martinelli", "Forward", "Arsenal", 39, "Brazil", "https://cdn.sofifa.net/players/251/566/24_120.png", 90),
    ("Marcus Rashford", "Forward", "Manchester United", 39, "England", "https://cdn.sofifa.net/players/231/677/24_120.png", 95),
    ("Rodrygo", "Forward", "Real Madrid", 140, "Brazil", "https://cdn.sofifa.net/players/243/812/24_120.png", 90),
    ("Sadio Mané", "Forward", "Al Nassr", 307, "Senegal", "https://cdn.sofifa.net/players/208/722/24_120.png", 90),
    ("Phil Foden", "Forward", "Manchester City", 39, "England", "https://cdn.sofifa.net/players/237/692/24_120.png", 95),
    ("Christopher Nkunku", "Forward", "Chelsea", 39, "France", "https://cdn.sofifa.net/players/232/418/24_120.png", 90),
    ("Riyad Mahrez", "Forward", "Al Ahli", 307, "Algeria", "https://cdn.sofifa.net/players/204/485/24_120.png", 85),
    ("Ousmane Dembélé", "Forward", "Paris Saint-Germain", 61, "France", "https://cdn.sofifa.net/players/231/443/24_120.png", 85),
    ("Kingsley Coman", "Forward", "Bayern Munich", 78, "France", "https://cdn.sofifa.net/players/213/345/24_120.png", 85),
    ("Julián Álvarez", "Forward", "Manchester City", 39, "Argentina", "https://cdn.sofifa.net/players/246/191/24_120.png", 95),
    ("Gabriel Jesus", "Forward", "Arsenal", 39, "Brazil", "https://cdn.sofifa.net/players/230/666/24_120.png", 90),
    ("Paulo Dybala", "Forward", "AS Roma", 135, "Argentina", "https://cdn.sofifa.net/players/211/110/24_120.png", 90),
    ("Lamine Yamal", "Forward", "FC Barcelona", 140, "Spain", "https://cdn.sofifa.net/players/277/643/24_120.png", 85),
    ("Luis Suárez", "Forward", "Inter Miami", 253, "Uruguay", "https://cdn.sofifa.net/players/176/580/24_120.png", 80),
    ("Alexis Sánchez", "Forward", "Udinese", 135, "Chile", "https://cdn.sofifa.net/players/184/941/24_120.png", 70),
    ("Iago Aspas", "Forward", "Celta de Vigo", 140, "Spain", "https://cdn.sofifa.net/players/190/594/24_120.png", 75),
    ("Mikel Oyarzabal", "Forward", "Real Sociedad", 140, "Spain", "https://cdn.sofifa.net/players/230/142/24_120.png", 80),
    ("Ángel Di María", "Forward", "Benfica", 94, "Argentina", "https://cdn.sofifa.net/players/183/898/24_120.png", 80),
    ("Luis Díaz", "Forward", "Liverpool", 39, "Colombia", "https://cdn.sofifa.net/players/232/877/24_120.png", 90),
    ("Raphinha", "Forward", "FC Barcelona", 140, "Brazil", "https://cdn.sofifa.net/players/233/419/24_120.png", 85),
    ("Antony", "Forward", "Manchester United", 39, "Brazil", "https://cdn.sofifa.net/players/251/850/24_120.png", 70),
]

    print("Inserting extra star players with costs...")
    for p in extras:
        # The SQL query now includes the 'cost' column
        cursor.execute("""
            INSERT OR IGNORE INTO players (name, position, club, league_id, nationality, image_url, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, p)
    conn.commit()
    print("Extra star players inserted!")


# === MAIN EXECUTION ===
if __name__ == "__main__":
    # First, create the table structure
    create_players_table()

    # Second, fetch players from major leagues
    update_selected_leagues()

    # Finally, add the hand-picked stars to ensure they are included
    insert_extra_players()

    print("\nDatabase population complete!")
    conn.close()
