# external_systems.py
import psycopg  # Using psycopg for PostgreSQL
import requests
import os  # Used for getting database credentials from environment variables

# --- 1. In-Memory Cache ---
# Functions that use a global dictionary to simulate a cache.
_in_memory_cache = {}


def add_item_to_cache(key: str, value: any):
    print(f"CACHE: Adding item '{key}' to cache.")
    _in_memory_cache[key] = value


def get_item_from_cache(key: str) -> any:
    print(f"CACHE: Getting item '{key}' from cache.")
    return _in_memory_cache.get(key)


def clear_cache():
    print("CACHE: Clearing the cache.")
    _in_memory_cache.clear()


# --- 2. Real Database (PostgreSQL) ---
# Functions that connect to and fetch data from a PostgreSQL database.
def connect_to_database(conn_str: str) -> psycopg.Connection:
    """Connects to a PostgreSQL database."""
    print(f"DATABASE: Connecting to PostgreSQL...")
    try:
        # Establish the connection
        conn = psycopg.connect(conn_str)
        return conn
    except psycopg.OperationalError as e:
        print(f"DATABASE: Connection failed: {e}")
        print(
            "Please ensure PostgreSQL is running and the connection string is correct."
        )
        raise


def setup_database(db_connection: psycopg.Connection):
    """Creates a 'users' table and inserts a sample user."""
    print("DATABASE: Setting up the database table...")
    with db_connection.cursor() as cur:
        # Drop table if it exists to make the script runnable multiple times
        cur.execute("DROP TABLE IF EXISTS users")
        # Create table
        cur.execute(
            """
                    CREATE TABLE users (
                                           id INTEGER PRIMARY KEY,
                                           name TEXT NOT NULL,
                                           email TEXT NOT NULL
                    )
                    """
        )
        # Insert a sample user
        cur.execute(
            "INSERT INTO users (id, name, email) VALUES (%s, %s, %s)",
            (101, "Alice", "alice@example.com"),
        )
        # Make the changes to the database persistent
        db_connection.commit()
    print("DATABASE: Setup complete.")


def get_user_from_db(user_id: int, db_connection: psycopg.Connection) -> dict:
    """Fetches a user from the database by their ID."""
    print(f"DATABASE: Querying for user_id: {user_id}")
    with db_connection.cursor() as cur:
        cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()

    if row:
        # Convert the tuple result into a dictionary
        user_data = {"user_id": row[0], "name": row[1], "email": row[2]}
        print(f"DATABASE: Found user: {user_data}")
        return user_data
    else:
        print(f"DATABASE: User with id {user_id} not found.")
        return None


# --- 3. Real Network API Call (Weather) ---
# A function that makes a real network request to a public weather API.
def get_weather_data(city: str) -> dict:
    """Fetches weather data from the Open-Meteo API."""
    # Step 1: Get coordinates for the city using the Open-Meteo Geocoding API
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1}
    print(f"NETWORK: Getting coordinates for {city}...")
    try:
        geo_res = requests.get(geo_url, params=geo_params, timeout=10)
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        if not geo_data.get("results"):
            return {"error": f"Could not find coordinates for city: {city}"}

        location = geo_data["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        print(f"NETWORK: Found coordinates: Lat={lat}, Lon={lon}")

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to geocoding service: {e}"}

    # Step 2: Get the weather for the coordinates
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
    print(f"NETWORK: Getting weather for {city}...")
    try:
        weather_res = requests.get(weather_url, params=weather_params, timeout=10)
        weather_res.raise_for_status()
        return weather_res.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to weather service: {e}"}


def run_examples():
    # --- Example Usage ---
    print("--- Running examples ---")

    # Cache example
    print("\n1. Testing Cache Functions:")
    add_item_to_cache("user_session", "session_token_xyz")
    retrieved_item = get_item_from_cache("user_session")
    print(f"Retrieved: {retrieved_item}")
    clear_cache()
    print(f"Retrieved after clearing: {get_item_from_cache('user_session')}")

    # --- Database Example ---
    # IMPORTANT: This requires a running PostgreSQL server and a valid connection string.
    # You can set the connection string as an environment variable named 'DB_CONN_STR'.
    # Example: "dbname=test user=postgres password=secret host=localhost"
    print("\n2. Testing Database Functions:")
    db_connection_string = (
        "dbname=randyzhu user=randyzhu password=randyzhu host=localhost"
    )
    if db_connection_string:
        try:
            db_conn = connect_to_database(db_connection_string)
            setup_database(db_conn)
            user = get_user_from_db(101, db_conn)
            print(f"Found user: {user}")
            non_existent_user = get_user_from_db(999, db_conn)
            print(f"Found user: {non_existent_user}")
            db_conn.close()
        except Exception as e:
            print(f"An error occurred during the database example: {e}")
    else:
        print("Skipping database example: Environment variable DB_CONN_STR not set.")

    # --- Network Example ---
    print("\n3. Testing Network Function:")
    weather = get_weather_data("Montreal")
    print(f"Weather in Montreal: {weather}")
