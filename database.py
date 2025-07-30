import sqlite3
import os

# Store DB file in the same folder as this module
DB_PATH = os.path.join(os.path.dirname(__file__), 'parking_app.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    # Return rows as tuples by default; set row_factory if you want dict-like access
    # conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # USERS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','user'))
        );
    ''')

    # PARKING LOTS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prime_location_name TEXT NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            price REAL NOT NULL,
            max_spots INTEGER NOT NULL
        );
    ''')

    # PARKING SPOTS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('A','O')),
            FOREIGN KEY (lot_id) REFERENCES parking_lots(id) ON DELETE CASCADE
        );
    ''')

    # BOOKINGS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vehicle_number TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            total_cost REAL,
            FOREIGN KEY (spot_id) REFERENCES parking_spots(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    # Insert default admin (only if no admin exists)
    c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1;")
    if not c.fetchone():
        c.execute('''
            INSERT INTO users (username, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@parking.com', 'admin123', 'admin'))  # TODO: hash password

    conn.commit()
    conn.close()


# --- Basic user helpers used by app.py --- #
def add_user(username, email, password, role='user'):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (username, email, password, role)
        VALUES (?, ?, ?, ?)
    ''', (username, email, password, role))
    conn.commit()
    conn.close()


def find_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, password, role FROM users WHERE email=?;', (email,))
    user = c.fetchone()
    conn.close()
    return user


# Allow standalone table creation
if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully.")