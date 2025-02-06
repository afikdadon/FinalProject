"""
db_utils.py
-----------
Description:
    Database utility functions for the Geometric Learning System. This module handles
    all database connections and user authentication operations, providing a clean
    interface for database interactions throughout the application.

Main Components:
    - Database Connection Management
    - User Authentication
    - User Creation and Management
    - Password Hashing and Verification

Author: Karin Hershko and Afik Dadon
Date: February 2024
"""

import pyodbc
from db_config import DB_CONFIG
from extensions import bcrypt
from typing import Optional, Dict


def get_db_connection():
    """Create and return a connection to the database using configuration parameters."""
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    )
    return pyodbc.connect(conn_str)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_user(email: str, password: str) -> Optional[Dict]:
    """Verify user credentials and return user information if valid."""
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
            return None

    except Exception as e:
        print(f"Database error in verify_user: {str(e)}")
        return None


def create_user(first_name: str, last_name: str, email: str, password: str) -> bool:
    """Create a new user in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check for existing user
            cursor.execute("SELECT email FROM Users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False

            # Insert new user
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


def verify_email_exists(email: str) -> bool:
    """Check if an email address already exists in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM Users WHERE email = ?', (email,))
            return bool(cursor.fetchone())

    except Exception as e:
        print(f"Database error in verify_email_exists: {str(e)}")
        return False