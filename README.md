# SquadBuilder: A Fantasy Football Web Application
================================================

#### Video Demo: <[URL](https://youtu.be/i5vF1Kje2Ho)>

#### Description:

SquadBuilder is a full-stack web application designed for football (soccer) enthusiasts, developed as a final project for CS50x. It provides a platform for users to register, log in, and create their own custom football squads. The application features two distinct modes of team creation: a budget-constrained "Fantasy Team" and an unrestricted "Dream Team." Beyond creation, it fosters a community environment where users can browse, view, rate, and comment on squads built by others, creating a dynamic and interactive social experience.

The project is built using Python with the Flask framework on the backend, a SQLite database for data persistence, and a dynamic frontend powered by HTML, Bootstrap 5, and vanilla JavaScript. It demonstrates a comprehensive understanding of web development principles, including user authentication, database management, interactive client-side scripting, and RESTful API design patterns for features like rating and commenting.

##### Core Features

-   **User Authentication:** Secure user registration and login system with password hashing. Logged-in users have access to a personal dashboard and social features.

-   **Dual Team Creation Modes:**

    -   **Fantasy Team:** Users are given a fixed budget (e.g., $700M) to assemble a squad of 11 players, requiring strategic choices based on player costs.

    -   **Dream Team:** Users can create a squad with any 11 players they desire, without any budget limitations.

-   **Interactive Lineup Builder:** A visually engaging interface featuring a football pitch where users can place players. Key features include:

    -   **Formation Selection:** Users can choose from various popular formations (e.g., 4-4-2, 4-3-3, 4-2-4), which dynamically updates the player slots on the pitch.

    -   **Live Player Search:** An instant search bar on the player selection panel allows users to filter the extensive player list in real-time.

    -   **Positional Filtering:** The player list can be filtered by position (Goalkeeper, Defender, Midfielder, Forward) to make selection easier.

    -   **Dynamic Budget Tracking:** For fantasy teams, the remaining budget updates instantly as players are added or removed.

-   **Community Hub ("Explore" Page):**

    -   A gallery displaying all teams created by the community.

    -   Live search functionality to filter teams by the creator's username as you type.

-   **Social Interaction:**

    -   **Team Viewing:** Each team has a dedicated page displaying its lineup in the saved formation on a pitch background.

    -   **Rating System:** Logged-in users can rate other users' teams on a scale of 1 to 10 stars. The system prevents users from rating their own teams or rating the same team multiple times (allowing edits instead).

    -   **Commenting:** In addition to a star rating, users can leave comments on teams to provide feedback or praise.

    -   **Squad Management:** Users can delete their own created squads from their personal dashboard.

##### Project Structure & File Descriptions

The project is organized into several key files and directories, each serving a distinct purpose.

-   **`app.py`**: This is the core of the application, containing all the backend logic. It's a Flask application that defines all the routes and handles all requests.

    -   **Routes:** It includes routes for user authentication (`/login`, `/register`, `/logout`), main pages (`/`, `/dashboard`, `/explore`), team management (`/create_team`, `/team/<id>`, `/delete_team`), and API-like endpoints for social features (`/rate_team`).

    -   **Database Interaction:** It manages all communication with the `players.db` database, executing SQL queries to fetch, insert, update, and delete data.

-   **`api_fetch.py`**: A standalone utility script responsible for populating the `players` table in the database.

    -   **API Integration:** It fetches player data from an external sports API for several major leagues.

    -   **Dynamic Cost Calculation:** It contains a helper function to dynamically assign a fantasy "cost" to players based on their performance rating from the API.

    -   **Manual Data:** It includes a manually curated list of "extra" players to ensure key superstars or players from other leagues are included, and to allow for custom data like local image paths.

-   **`players.db`**: The SQLite database that stores all persistent data for the application. The schema is designed to be relational and efficient:

    -   `users`: Stores user credentials (`id`, `username`, `hash`).

    -   `players`: A master list of all available players (`id`, `name`, `position`, `club`, `image_url`, `cost`).

    -   `user_teams`: Contains information about each created squad (`id`, `user_id`, `team_name`, `team_type`, `total_cost`, `formation`).

    -   `team_rosters`: A linking table that connects players to teams, representing a many-to-many relationship.

    -   `team_ratings`: Stores every rating and comment, with a `UNIQUE` constraint on `(user_id, team_id)` to ensure a user can only review a specific team once.

-   **`templates/`**: This directory contains all the HTML files that are rendered by Flask.

    -   `layout.html`: The base template providing a consistent navigation bar, footer, and structure for all other pages.

    -   `create_team.html`: The most complex frontend page. It uses extensive JavaScript to provide the interactive team-building experience, including live player filtering and dynamic budget updates, all without reloading the page.

    -   `explore.html`: The community page, which also uses JavaScript for its live search functionality. It receives a full list of teams from the backend and performs filtering client-side for a fast, responsive feel.

    -   `team_view.html`: Displays a finished squad. It uses JavaScript to handle the interactive star rating and comment submission via an asynchronous `fetch()` request to the backend.

-   **`static/`**: This directory holds all static assets.

    -   `images/`: Contains background images for the pitch (`fantasy.jpg`, `dream.jpg`) and any locally saved player photos.

    -   `styles.css`: (Optional) For any custom CSS rules that extend the Bootstrap framework.

##### Design Choices

Several key design decisions were made to enhance the user experience and application performance:

-   **Client-Side Filtering:** For the `create_team` and `explore` pages, I opted for client-side JavaScript filtering instead of server-side. The backend sends the entire dataset (all players or all teams) to the frontend once. The JavaScript then handles all subsequent searches and filters instantly in the browser. This provides a much faster and more "app-like" experience for the user, as it eliminates the need for page reloads on every search query.

-   **Hybrid Data Sourcing:** Relying solely on a free API can be limiting. The choice to use a hybrid approach in `api_fetch.py`---combining bulk API data with a manually maintained list of star players---provides greater control and flexibility. It ensures that iconic players are always available and allows for custom data, such as local image URLs or precisely balanced fantasy costs.

-   **RESTful Interaction for Ratings:** The rating and commenting system uses a `fetch()` request from the frontend to a dedicated `/rate_team` endpoint on the backend. This asynchronous approach means the user can submit their review without the entire page having to reload, providing instant feedback and a smoother interaction.

-   **Database Efficiency:** The database schema was designed with relational principles in mind. Using a `UNIQUE` constraint in the `team_ratings` table offloads the logic of preventing duplicate ratings to the database itself, which is more efficient and reliable than checking for existence with a `SELECT` query before every `INSERT`. The logic in `app.py` leverages this to perform an "upsert" (update or insert) operation.
