# db_utils.py
import pyodbc
from db_config import DB_CONFIG
from extensions import bcrypt

def get_db_connection():
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)

def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_user(email, password):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, first_name, last_name, email, 
                       password_hash, role 
                FROM Users 
                WHERE email = ?""", (email,))
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user.password_hash, password):
                return {
                    'user_id': user.user_id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': email,
                    'role': user.role
                }
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None


def create_user(first_name, last_name, email, password):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Debug print
            cursor.execute("SELECT COUNT(*) FROM Users")
            count = cursor.fetchone()[0]
            print(f"Total users in database: {count}")

            cursor.execute("SELECT email FROM Users WHERE email = ?", (email,))
            existing_user = cursor.fetchone()
            print(f"Existing user check result: {existing_user}")

            if existing_user:
                return False

            # Insert user
            cursor.execute(
                """INSERT INTO Users (first_name, last_name, email, password_hash, role, created_at) 
                   VALUES (?, ?, ?, ?, 'user', GETDATE())""",
                (first_name, last_name, email, password)
            )
            conn.commit()
            return True

    except Exception as e:
        print(f"Database error in create_user: {str(e)}")
        return False