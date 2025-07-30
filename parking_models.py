import sqlite3
from datetime import datetime
import os

# Use the same DB file as database.py
DB_PATH = os.path.join(os.path.dirname(__file__), 'parking_app.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ------------------- USERS ------------------- #
def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, role FROM users WHERE role='user';")
    rows = c.fetchall()
    conn.close()
    return rows


# ------------------- PARKING LOTS ------------------- #
def add_parking_lot(name, address, pin_code, price, max_spots):
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        INSERT INTO parking_lots (
            prime_location_name, address, pin_code, price, max_spots
        ) VALUES (?, ?, ?, ?, ?);
    ''', (name, address, pin_code, price, max_spots))

    lot_id = c.lastrowid

    # Auto-create parking spots
    for _ in range(max_spots):
        c.execute("INSERT INTO parking_spots (lot_id, status) VALUES (?, 'A');", (lot_id,))

    conn.commit()
    conn.close()
    return lot_id


def get_all_lots():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM parking_lots;")
    lots = c.fetchall()
    conn.close()
    return lots


def delete_parking_lot(lot_id):
    conn = get_connection()
    c = conn.cursor()

    # Prevent delete if any spot is occupied
    c.execute("SELECT COUNT(*) FROM parking_spots WHERE lot_id=? AND status='O';", (lot_id,))
    occupied = c.fetchone()[0]
    if occupied > 0:
        conn.close()
        return False

    c.execute("DELETE FROM parking_spots WHERE lot_id=?;", (lot_id,))
    c.execute("DELETE FROM parking_lots WHERE id=?;", (lot_id,))
    conn.commit()
    conn.close()
    return True


# ------------------- PARKING SPOTS ------------------- #
def get_spots_by_lot(lot_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM parking_spots WHERE lot_id=?;", (lot_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_available_spot(lot_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM parking_spots WHERE lot_id=? AND status='A' LIMIT 1;", (lot_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def update_spot_status(spot_id, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE parking_spots SET status=? WHERE id=?;", (status, spot_id))
    conn.commit()
    conn.close()


# ------------------- BOOKINGS ------------------- #
def get_lot_price_by_spot(spot_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT price
        FROM parking_lots
        WHERE id = (SELECT lot_id FROM parking_spots WHERE id=?);
    ''', (spot_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0.0


def book_spot(user_id, lot_id, vehicle_number):
    """Assign the first available spot in the given lot; return spot_id or None."""
    spot_id = get_available_spot(lot_id)
    if not spot_id:
        return None

    conn = get_connection()
    c = conn.cursor()
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('''
        INSERT INTO bookings (spot_id, user_id, vehicle_number, start_time)
        VALUES (?, ?, ?, ?);
    ''', (spot_id, user_id, vehicle_number, start_time))

    conn.commit()
    conn.close()

    # Update spot status in a separate connection (keeps code simple)
    update_spot_status(spot_id, 'O')
    return spot_id


def release_spot(booking_id):
    """Close a booking, free the spot, and return total cost. Returns None if invalid."""
    conn = get_connection()
    c = conn.cursor()
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute("SELECT spot_id, start_time FROM bookings WHERE id=? AND end_time IS NULL;", (booking_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None

    spot_id, start_time = row

    # Cost calculation
    start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    hours = (end_dt - start_dt).total_seconds() / 3600
    price_per_hour = get_lot_price_by_spot(spot_id)
    total_cost = round(hours * price_per_hour, 2)

    c.execute("UPDATE bookings SET end_time=?, total_cost=? WHERE id=?;", (end_time, total_cost, booking_id))
    conn.commit()
    conn.close()

    update_spot_status(spot_id, 'A')
    return total_cost


def get_user_bookings(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT b.id, b.spot_id, b.vehicle_number, b.start_time, b.end_time, b.total_cost
        FROM bookings b
        WHERE b.user_id=?;
    ''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ------------------- ANALYTICS FOR CHARTS ------------------- #

def get_user_count():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role='user';")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_lot_usage_summary():
    """Returns list of (lot_name, total_spots, occupied_spots)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT 
            pl.prime_location_name,
            pl.max_spots,
            COUNT(ps.id) FILTER (WHERE ps.status = 'O') AS occupied
        FROM parking_lots pl
        LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
        GROUP BY pl.id;
    ''')
    data = c.fetchall()
    conn.close()
    return data


def get_monthly_booking_summary():
    """Returns number of bookings for each of the last 6 months"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT strftime('%Y-%m', start_time) as month, COUNT(*)
        FROM bookings
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6;
    ''')
    rows = c.fetchall()
    conn.close()
    return rows[::-1]  # Reverse for ascending order

def get_booked_spots_count(lot_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*)
        FROM parking_spots ps
        JOIN parking_lots pl ON ps.lot_id = pl.id
        WHERE pl.prime_location_name = ? AND ps.status = 'O';
    """, (lot_name,))
    count = c.fetchone()[0]
    conn.close()
    return count
def get_daily_bookings():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT DATE(timestamp) as booking_date, COUNT(*) 
        FROM bookings 
        GROUP BY booking_date
        ORDER BY booking_date ASC
    """)
    
    result = c.fetchall()
    conn.close()
    return result 