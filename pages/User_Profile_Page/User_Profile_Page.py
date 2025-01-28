from flask import Blueprint, render_template, session, redirect, url_for
from db_utils import get_db_connection

user_profile_page = Blueprint('user_profile_page', __name__,
                              template_folder='templates',
                              static_folder='static')

from flask import Blueprint, render_template, session, redirect, url_for
from db_utils import get_db_connection

user_profile_page = Blueprint('user_profile_page', __name__,
                              template_folder='templates',
                              static_folder='static')


@user_profile_page.route('/')
def profile():
    # Get user from session
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page.login'))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get user stats
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) 
                     FROM UserLogs 
                     WHERE user_id = ? AND action_type = 'SESSION_START') as total_sessions,
                    (SELECT COUNT(*) 
                     FROM UserLogs 
                     WHERE user_id = ? AND action_type = 'SESSION_END') as completed_sessions,
                    (SELECT COUNT(*) 
                     FROM UserLogs 
                     WHERE user_id = ? AND action_type = 'LOGIN_ATTEMPT') as login_count
            """, (user['user_id'], user['user_id'], user['user_id']))

            user_stats = cursor.fetchone()

            # Get recent activity
            cursor.execute("""
                SELECT TOP 5 
                    timestamp, 
                    action_type, 
                    action_data
                FROM UserLogs
                WHERE user_id = ?
                ORDER BY timestamp DESC
            """, (user['user_id'],))

            recent_activity = cursor.fetchall()

            return render_template('User_Profile_Page.html',
                                   user=user,
                                   user_stats=user_stats,
                                   recent_activity=recent_activity)

    except Exception as e:
        print(f"Error in profile route: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('login_page.login'))