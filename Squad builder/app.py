import os
import sqlite3
from flask import Flask, flash, url_for, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
# --- HELPER FUNCTION (from CS50) ---
def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# --- FLASK APP CONFIGURATION ---
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database connection
# This makes the database connection return dictionaries, which is easier to work with
def get_db_connection():
    conn = sqlite3.connect("players.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- FORMATION DATA (used for displaying teams) ---
FORMATIONS = {
    '4-4-2': [
        {'top': '88%', 'left': '50%'}, {'top': '70%', 'left': '15%'}, {'top': '70%', 'left': '35%'},
        {'top': '70%', 'left': '65%'}, {'top': '70%', 'left': '85%'}, {'top': '45%', 'left': '15%'},
        {'top': '45%', 'left': '35%'}, {'top': '45%', 'left': '65%'}, {'top': '45%', 'left': '85%'},
        {'top': '20%', 'left': '35%'}, {'top': '20%', 'left': '65%'}
    ],
    '4-3-3': [
        {'top': '88%', 'left': '50%'}, {'top': '70%', 'left': '15%'}, {'top': '70%', 'left': '35%'},
        {'top': '70%', 'left': '65%'}, {'top': '70%', 'left': '85%'}, {'top': '50%', 'left': '25%'},
        {'top': '50%', 'left': '50%'}, {'top': '50%', 'left': '75%'}, {'top': '20%', 'left': '20%'},
        {'top': '15%', 'left': '50%'}, {'top': '20%', 'left': '80%'}
    ],
    '3-4-3': [
        {'top': '88%', 'left': '50%'}, {'top': '70%', 'left': '25%'}, {'top': '70%', 'left': '50%'},
        {'top': '70%', 'left': '75%'}, {'top': '45%', 'left': '15%'}, {'top': '45%', 'left': '35%'},
        {'top': '45%', 'left': '65%'}, {'top': '45%', 'left': '85%'}, {'top': '20%', 'left': '20%'},
        {'top': '15%', 'left': '50%'}, {'top': '20%', 'left': '80%'}
    ],
    '5-3-2': [
        {'top': '88%', 'left': '50%'}, {'top': '70%', 'left': '10%'}, {'top': '70%', 'left': '30%'},
        {'top': '70%', 'left': '50%'}, {'top': '70%', 'left': '70%'}, {'top': '70%', 'left': '90%'},
        {'top': '45%', 'left': '25%'}, {'top': '45%', 'left': '50%'}, {'top': '45%', 'left': '75%'},
        {'top': '20%', 'left': '35%'}, {'top': '20%', 'left': '65%'}
    ],
     '4-2-3-1': [
        {'top': '88%', 'left': '50%'}, {'top': '75%', 'left': '15%'}, {'top': '75%', 'left': '35%'},
        {'top': '75%', 'left': '65%'}, {'top': '75%', 'left': '85%'}, {'top': '55%', 'left': '35%'},
        {'top': '55%', 'left': '65%'}, {'top': '35%', 'left': '20%'}, {'top': '35%', 'left': '50%'},
        {'top': '35%', 'left': '80%'}, {'top': '15%', 'left': '50%'}
    ],
    '4-2-4': [
        {'top': '88%', 'left': '50%'}, {'top': '70%', 'left': '15%'}, {'top': '70%', 'left': '35%'},
        {'top': '70%', 'left': '65%'}, {'top': '70%', 'left': '85%'}, {'top': '50%', 'left': '35%'},
        {'top': '50%', 'left': '65%'}, {'top': '20%', 'left': '15%'}, {'top': '20%', 'left': '35%'},
        {'top': '20%', 'left': '65%'}, {'top': '20%', 'left': '85%'}
    ]
}

# --- MAIN ROUTES ---
@app.route("/")
def index():
    """Show homepage with top rated teams."""
    conn = get_db_connection()
    # Query to get teams, their creators, and their average rating, ordered by the best rating
    rows = conn.execute("""
        SELECT t.id, t.team_name, t.team_type, t.created_at, u.username,
               AVG(r.rating_value) as avg_rating
        FROM user_teams t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN team_ratings r ON t.id = r.team_id
        GROUP BY t.id
        ORDER BY avg_rating DESC
        LIMIT 6
    """).fetchall()
    conn.close()
    top_teams = []
    for row in rows:
        team = dict(row)
        # Convert the string from the DB to a datetime object
        team['created_at'] = datetime.strptime(team['created_at'], '%Y-%m-%d %H:%M:%S')
        top_teams.append(team)
    return render_template("index.html", top_teams=top_teams)


@app.route("/dashboard")
@login_required
def dashboard():
    """Show user's dashboard with their created teams."""
    conn = get_db_connection()
    # Get all teams created by the current user
    rows = conn.execute("""
        SELECT t.id, t.team_name, t.team_type, t.total_cost, t.created_at,
               AVG(r.rating_value) as avg_rating
        FROM user_teams t
        LEFT JOIN team_ratings r ON t.id = r.team_id
        WHERE t.user_id = ?
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """, (session["user_id"],)).fetchall()
    conn.close()
    user_teams = []
    for row in rows:
        team = dict(row)
        # Convert the string from the DB to a datetime object
        team['created_at'] = datetime.strptime(team['created_at'], '%Y-%m-%d %H:%M:%S')
        user_teams.append(team)
    return render_template("dashboard.html", user_teams=user_teams)


@app.route("/create_team", methods=["GET", "POST"])
@login_required
def create_team():
    conn = get_db_connection()
    """Create a new fantasy or dream team."""
    team_type_param = request.args.get("type", request.form.get("team_type", "fantasy"))
    if team_type_param not in ["fantasy", "dream"]:
        flash("Invalid team type specified.", "danger")
        return redirect(url_for('dashboard'))
    background = ""
    if team_type_param == "fantasy":
        background = "/static/images/fantasy.jpg"
    elif team_type_param == "dream":
        background = "/static/images/dream.jpg"

    if request.method == "POST":
        team_name = request.form.get("team_name")
        team_type = request.form.get("team_type")
        player_ids_str = request.form.get("player_ids")
        formation=request.form.get("formation")

        # Validation
        if not team_name:
            flash("Team name is required.", "danger")
            return redirect(request.url)
        if not player_ids_str:
            flash("No players were selected.", "danger")
            return redirect(request.url)

        player_ids = [int(pid) for pid in player_ids_str.split(',')]
        if len(player_ids) != 11:
            flash("You must select exactly 11 players.", "danger")
            return redirect(request.url)

        total_cost = 0
        if team_type == 'fantasy':
            # Calculate total cost for fantasy team and validate budget
            placeholders = ','.join('?' for _ in player_ids)
            costs = conn.execute(f"SELECT cost FROM players WHERE id IN ({placeholders})", player_ids).fetchall()
            total_cost = sum(row['cost'] for row in costs)
            if total_cost > 700:
                flash(f"Your team cost (${total_cost}M) exceeds the $700M budget.", "danger")
                return redirect(request.url)

        # Insert new team into database
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_teams (user_id, team_name, team_type, total_cost, formation) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], team_name, team_type, total_cost if team_type == 'fantasy' else None, formation)
        )
        team_id = cursor.lastrowid

        # Insert players into the roster
        for player_id in player_ids:
            cursor.execute("INSERT INTO team_rosters (team_id, player_id) VALUES (?, ?)", (team_id, player_id))

        conn.commit()
        conn.close()
        flash("Team created successfully!", "success")
        return redirect("/dashboard")

    else: # GET request
        team_type = request.args.get("type", "fantasy")
        if team_type not in ['fantasy', 'dream']:
            return "Invalid team type", 400

        player_rows = conn.execute("SELECT * FROM players ORDER BY cost DESC").fetchall()
        conn.close()

        # Convert list of Row objects into a list of dictionaries to make it JSON serializable
        players = [dict(row) for row in player_rows]

        return render_template("create_team.html", players=players, team_type=team_type_param, background=background)

@app.route("/explore")
def explore():
    """Show all community teams, prepped for client-side search."""
    conn = get_db_connection()
    # Fetch ALL teams, always. The filtering will be done in JavaScript.
    rows = conn.execute("""
        SELECT t.id, t.team_name, t.team_type, t.created_at, u.username,
               AVG(r.rating_value) as avg_rating
        FROM user_teams t
        JOIN users u ON t.user_id = u.id
        LEFT JOIN team_ratings r ON t.id = r.team_id
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """).fetchall()
    conn.close()

    all_teams = []
    for row in rows:
        team = dict(row)
        # Pre-format the date into a user-friendly string for JavaScript
        if team['created_at']:
            date_obj = datetime.strptime(team['created_at'], '%Y-%m-%d %H:%M:%S')
            team['created_at_formatted'] = date_obj.strftime('%b %d, %Y')
        else:
            team['created_at_formatted'] = 'N/A'
        all_teams.append(team)

    return render_template("explore.html", all_teams=all_teams)


@app.route("/team/<int:team_id>")
def team_view(team_id):
    """Display a single team's lineup and rating."""
    conn = get_db_connection()

    # Get team details
    team = conn.execute("""
        SELECT t.*, u.username
        FROM user_teams t
        JOIN users u ON t.user_id = u.id
        WHERE t.id = ?
    """, (team_id,)).fetchone()
    if not team:
        return "Team not found", 404
    team_type = team['team_type']
    background = ""
    if team_type == "fantasy":
        background = "/static/images/fantasy.jpg"
    elif team_type == "dream":
        background = "/static/images/dream.jpg"

    # Get roster of players, ordered by position for consistent display
    roster = conn.execute("""
        SELECT p.*
        FROM players p
        JOIN team_rosters tr ON p.id = tr.player_id
        WHERE tr.team_id = ?
        ORDER BY
            CASE p.position
                WHEN 'Goalkeeper' THEN 1
                WHEN 'Defender' THEN 2
                WHEN 'Midfielder' THEN 3
                WHEN 'Forward' THEN 4
                ELSE 5
            END
    """, (team_id,)).fetchall()

    # Combine roster with a default formation for display
    formation_coords = FORMATIONS.get(team['formation'], FORMATIONS['4-4-2']) # Default to 4-4-2 for viewing
    roster_with_formation = []
    for i, player in enumerate(roster):
        if i < len(formation_coords):
            player_dict = dict(player) # Convert sqlite3.Row to dict
            player_dict.update(formation_coords[i])
            roster_with_formation.append(player_dict)

    # Get average rating and number of ratings
    rating_data = conn.execute("""
        SELECT AVG(rating_value) as avg_rating, COUNT(rating_value) as num_ratings
        FROM team_ratings
        WHERE team_id = ?
    """, (team_id,)).fetchone()
    user_rating_info = None
    if session.get("user_id"):
        rating_record = conn.execute(
            "SELECT rating_value FROM team_ratings WHERE user_id = ? AND team_id = ?",
            (session["user_id"], team_id)
        ).fetchone()
        if rating_record:
            user_rating_info = dict(rating_record)
    comments = conn.execute("""
        SELECT r.comment, u.username FROM team_ratings r JOIN users u ON r.user_id = u.id
        WHERE r.team_id = ? AND r.comment IS NOT NULL AND r.comment != ''
        ORDER BY r.id DESC
    """, (team_id,)).fetchall()

    # Check if the current logged-in user has already rated this team

    conn.close()
    return render_template(
        "team_view.html",
        team=team,
        roster_with_formation=roster_with_formation,
        avg_rating=rating_data['avg_rating'],
        num_ratings=rating_data['num_ratings'],
        user_rating_info=user_rating_info,
        comments=comments,
        background=background
    )
@app.route("/delete_team/<int:team_id>", methods=["POST"])
@login_required
def delete_team(team_id):
    """Delete a user's saved squad."""
    conn = get_db_connection()

    # First, verify the user owns the team they are trying to delete
    team = conn.execute("SELECT user_id FROM user_teams WHERE id = ?", (team_id,)).fetchone()

    if team is None:
        flash("Team not found.", "danger")
        conn.close()
        return redirect("/dashboard")

    if team['user_id'] != session['user_id']:
        # If the user is not the owner, deny permission
        flash("You do not have permission to delete this team.", "danger")
        conn.close()
        return redirect("/dashboard")

    # If checks pass, proceed with deletion
    cursor = conn.cursor()
    # Important: Delete from tables with foreign key dependencies first
    cursor.execute("DELETE FROM team_ratings WHERE team_id = ?", (team_id,))
    cursor.execute("DELETE FROM team_rosters WHERE team_id = ?", (team_id,))

    # Finally, delete the team itself from the parent table
    cursor.execute("DELETE FROM user_teams WHERE id = ?", (team_id,))

    conn.commit()
    conn.close()

    flash("Team deleted successfully.", "success")
    return redirect("/dashboard")



@app.route("/rate_team/<int:team_id>", methods=["POST"])
@login_required
def rate_team(team_id):
    """Handle a user submitting a rating for a team."""
    conn = get_db_connection()
    data = request.get_json()
    rating_value = request.json.get("rating")
    comment_text = data.get("comment", "").strip()

    if not rating_value or not 1 <= int(rating_value) <= 10:
        return jsonify({"success": False, "message": "Invalid rating value."}), 400

    # Check if user is trying to rate their own team
    team_owner_id = conn.execute("SELECT user_id FROM user_teams WHERE id = ?", (team_id,)).fetchone()['user_id']
    if team_owner_id == session["user_id"]:
        return jsonify({"success": False, "message": "You cannot rate your own team."}), 403

    # Use INSERT OR IGNORE and then UPDATE to handle both new and existing ratings
    # This is an alternative to the try/except block and is common in SQLite
    existing_rating = conn.execute("SELECT id FROM team_ratings WHERE user_id = ? AND team_id = ?", (session["user_id"], team_id)).fetchone()
    cursor = conn.cursor()
    if existing_rating:
        # Update existing rating and comment
        cursor.execute(
            "UPDATE team_ratings SET rating_value = ?, comment = ? WHERE user_id = ? AND team_id = ?",
            (rating_value, comment_text, session["user_id"], team_id)
        )
    else:
        # Insert new rating and comment
        cursor.execute(
            "INSERT INTO team_ratings (user_id, team_id, rating_value, comment) VALUES (?, ?, ?, ?)",
            (session["user_id"], team_id, rating_value, comment_text)
        )

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Rating saved successfully."})


# --- AUTHENTICATION ROUTES ---
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Must provide username and password", "danger")
            return render_template("login.html")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["hash"], password):
            flash("Invalid username and/or password", "danger")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Welcome back, {user['username']}!", "success")
        return redirect("/dashboard")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            flash("All fields are required.", "danger")
            return render_template("register.html")
        if password != confirmation:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        conn = get_db_connection()
        user_exists = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user_exists:
            flash("Username is already taken.", "danger")
            conn.close()
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()

        # Log the new user in automatically
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash("Registered successfully!", "success")
        return redirect("/dashboard")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

