from flask import Blueprint, render_template, session, redirect, url_for
from db_utils import get_db_connection

user_profile_page = Blueprint('user_profile_page', __name__,
                           template_folder='templates',
                           static_folder='static')

@user_profile_page.route('/')
def profile():
   user = session.get('user')
   if not user:
       return redirect(url_for('login_page.login'))

   try:
       with get_db_connection() as conn:
           cursor = conn.cursor()

           # Basic user stats
           cursor.execute("""
               WITH UserSessions AS (
                   SELECT COUNT(*) as total_starts
                   FROM UserLogs 
                   WHERE user_id = ? AND action_type = 'SESSION_START'
               ),
               CompletedSessions AS (
                   SELECT COUNT(*) as total_completed
                   FROM UserLogs 
                   WHERE user_id = ? AND action_type = 'SESSION_END'
               ),
               LoginAttempts AS (
                   SELECT COUNT(*) as login_count
                   FROM UserLogs 
                   WHERE user_id = ? AND action_type = 'LOGIN_ATTEMPT'
               )
               SELECT 
                   ISNULL(UserSessions.total_starts, 0) as total_sessions,
                   CASE 
                       WHEN ISNULL(CompletedSessions.total_completed, 0) > ISNULL(UserSessions.total_starts, 0) 
                       THEN ISNULL(UserSessions.total_starts, 0)
                       ELSE ISNULL(CompletedSessions.total_completed, 0)
                   END as completed_sessions,
                   ISNULL(LoginAttempts.login_count, 0) as login_count
               FROM UserSessions
               CROSS JOIN CompletedSessions
               CROSS JOIN LoginAttempts
           """, (user['user_id'], user['user_id'], user['user_id']))
           user_stats = cursor.fetchone()

           # Recent activity (non-admin only)
           recent_activity = None
           if user['role'] != 'admin':
               cursor.execute("""
                   SELECT TOP 5 timestamp, action_type
                   FROM UserLogs
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
               """, (user['user_id'],))
               recent_activity = cursor.fetchall()

           # Admin statistics
           admin_stats = None
           if user['role'] == 'admin':
               # Basic system stats
               cursor.execute("""
                   SELECT 
                       (SELECT COUNT(*) FROM Users) as total_users,
                       (SELECT COUNT(DISTINCT user_id) 
                        FROM UserLogs 
                        WHERE timestamp >= DATEADD(day, -1, GETDATE())) as active_users_day,
                       (SELECT COUNT(DISTINCT user_id) 
                        FROM UserLogs 
                        WHERE timestamp >= DATEADD(day, -7, GETDATE())) as active_users_week,
                       (SELECT COUNT(*) 
                        FROM UserLogs 
                        WHERE action_type = 'SESSION_END' 
                        AND action_data LIKE '%"final_theorem_id"%'
                        AND action_data NOT LIKE '%"final_theorem_id": null%') as completed_exercises
               """)
               system_stats = cursor.fetchone()

               # Question analytics
               cursor.execute("""
                   SELECT 
                       q.question_id,
                       CAST(q.question_text AS VARCHAR(MAX)) as question_text,
                       q.difficulty_level,
                       COUNT(DISTINCT ul.user_id) as unique_users,
                       (SELECT COUNT(*) 
                        FROM UserLogs 
                        WHERE action_type = 'QUESTION_ANSWER' 
                        AND JSON_VALUE(action_data, '$.question_id') = CAST(q.question_id as VARCHAR)) as total_asked
                   FROM Questions q
                   LEFT JOIN UserLogs ul ON ul.action_type = 'QUESTION_ANSWER' 
                       AND JSON_VALUE(ul.action_data, '$.question_id') = CAST(q.question_id as VARCHAR)
                   WHERE q.active = 1
                   GROUP BY q.question_id, CAST(q.question_text AS VARCHAR(MAX)), q.difficulty_level
                   ORDER BY total_asked DESC
               """)
               question_analytics = cursor.fetchall()

               # Theorems data
               cursor.execute("""
                   SELECT t.theorem_id, t.theorem_text, t.category
                   FROM Theorems t
                   WHERE t.active = 1
                   ORDER BY t.theorem_id
               """)
               theorems_data = cursor.fetchall()

               admin_stats = {
                   'system_stats': system_stats,
                   'question_analytics': question_analytics,
                   'theorems': theorems_data
               }

           return render_template('User_Profile_Page.html',
                              user=user,
                              user_stats=user_stats,
                              recent_activity=recent_activity,
                              admin_stats=admin_stats)

   except Exception as e:
       print(f"Database error: {str(e)}")
       import traceback
       traceback.print_exc()
       return render_template('User_Profile_Page.html',
                          user=user,
                          user_stats=(0, 0, 0),
                          recent_activity=None,
                          admin_stats={'system_stats': (0, 0, 0, 0),
                                     'theorems': [],
                                     'question_analytics': []} if user['role'] == 'admin' else None)