from flask import Blueprint, render_template, session, redirect, url_for
from db_utils import get_db_connection

user_profile_page = Blueprint('user_profile_page', __name__,
                              template_folder='templates',
                              static_folder='static')


@user_profile_page.route('/')
def profile():
    # Check if user is logged in
    user = session.get('user')
    print(user)
    if not user:
        return redirect(url_for('login_page.login'))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get user activity logs
            cursor.execute("""
                SELECT TOP 10 timestamp, action_type, action_data
                FROM UserLogs
                WHERE user_id = ?
                ORDER BY timestamp DESC
            """, (user['user_id'],))

            activity_logs = cursor.fetchall()

            # If user is admin, get additional statistics
            admin_stats = None
            if user.get('role') == 'admin':
                # Get total users count
                cursor.execute("SELECT COUNT(*) FROM Users")
                total_users = cursor.fetchone()[0]

                # Get total sessions count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM UserLogs 
                    WHERE action_type = 'NEW_SESSION'
                """)
                total_sessions = cursor.fetchone()[0]

                # Get average sessions per user
                cursor.execute("""
                    SELECT COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT user_id), 0)
                    FROM UserLogs 
                    WHERE action_type = 'NEW_SESSION'
                """)
                avg_sessions = cursor.fetchone()[0] or 0

                admin_stats = {
                    'total_users': total_users,
                    'total_sessions': total_sessions,
                    'avg_sessions': round(avg_sessions, 2) if avg_sessions else 0
                }

            return render_template('User_Profile_Page.html',
                                   user=user,
                                   activity_logs=activity_logs,
                                   admin_stats=admin_stats)

    except Exception as e:
        print(f"Error in profile route: {str(e)}")
        return redirect(url_for('login_page.login'))