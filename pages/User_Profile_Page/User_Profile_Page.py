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
                SELECT 
                    (SELECT COUNT(*) FROM UserLogs WHERE user_id = ? AND action_type = 'SESSION_START') as total_sessions,
                    (SELECT COUNT(*) FROM UserLogs WHERE user_id = ? AND action_type = 'SESSION_END') as completed_sessions,
                    (SELECT COUNT(*) FROM UserLogs WHERE user_id = ? AND action_type = 'LOGIN_ATTEMPT') as login_count
            """, (user['user_id'], user['user_id'], user['user_id']))

            user_stats = cursor.fetchone()

            # Recent activity (only for non-admin users)
            recent_activity = None
            if user['role'] != 'admin':
                cursor.execute("""
                    SELECT TOP 5 timestamp, action_type
                    FROM UserLogs
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                """, (user['user_id'],))
                recent_activity = cursor.fetchall()

            # Admin stats
            admin_stats = None
            if user['role'] == 'admin':
                # System-wide statistics
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM Users) as total_users,
                        (SELECT COUNT(DISTINCT user_id) 
                         FROM UserLogs 
                         WHERE timestamp >= DATEADD(day, -1, GETDATE())) as active_users_day,
                        (SELECT COUNT(*) 
                         FROM UserLogs 
                         WHERE action_type = 'SESSION_START') as total_sessions,
                        (SELECT COUNT(*) 
                         FROM UserLogs 
                         WHERE action_type = 'SESSION_END') as completed_sessions
                """)
                system_stats = cursor.fetchone()

                # Triangle type distribution
                cursor.execute("""
                    SELECT 
                        t.triangle_id,
                        t.triangle_type,
                        (SELECT COUNT(*) 
                         FROM UserLogs ul 
                         WHERE ul.action_type = 'SESSION_END' 
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"final_theorem_id": ' + CAST(t.triangle_id AS VARCHAR) + '%'
                        ) as usage_count
                    FROM Triangles t
                    ORDER BY t.triangle_id
                """)
                triangle_stats = cursor.fetchall()

                # Get all theorems with triangle type names
                cursor.execute("""
                    SELECT t.theorem_id, t.theorem_text, t.category
                    FROM Theorems t
                    ORDER BY t.theorem_id
                """)
                theorems = cursor.fetchall()

                # Get all questions
                cursor.execute("""
                    SELECT question_id, question_text, difficulty_level 
                    FROM Questions 
                    ORDER BY question_id
                """)
                questions = cursor.fetchall()

                # Question statistics with all answer types
                cursor.execute("""
                    SELECT 
                        q.question_id,
                        q.question_text,
                        q.difficulty_level,
                        (SELECT COUNT(*) 
                         FROM UserLogs ul 
                         WHERE ul.action_type = 'QUESTION_ANSWER' 
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"question_id": ' + CAST(q.question_id AS VARCHAR) + '%'
                        ) as times_asked,
                        (SELECT COUNT(*) 
                         FROM UserLogs ul 
                         WHERE ul.action_type = 'QUESTION_ANSWER' 
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"question_id": ' + CAST(q.question_id AS VARCHAR) + '%'
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"answer": "כן"%'
                        ) as yes_count,
                        (SELECT COUNT(*) 
                         FROM UserLogs ul 
                         WHERE ul.action_type = 'QUESTION_ANSWER' 
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"question_id": ' + CAST(q.question_id AS VARCHAR) + '%'
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"answer": "לא"%'
                        ) as no_count,
                        (SELECT COUNT(*) 
                         FROM UserLogs ul 
                         WHERE ul.action_type = 'QUESTION_ANSWER' 
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"question_id": ' + CAST(q.question_id AS VARCHAR) + '%'
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"answer": "לא יודע"%'
                        ) as dont_know_count,
                        (SELECT COUNT(*) 
                         FROM UserLogs ul 
                         WHERE ul.action_type = 'QUESTION_ANSWER' 
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"question_id": ' + CAST(q.question_id AS VARCHAR) + '%'
                         AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"answer": "כנראה"%'
                        ) as probably_count
                    FROM Questions q
                    WHERE (SELECT COUNT(*) 
                           FROM UserLogs ul 
                           WHERE ul.action_type = 'QUESTION_ANSWER' 
                           AND CAST(ul.action_data AS NVARCHAR(MAX)) LIKE '%"question_id": ' + CAST(q.question_id AS VARCHAR) + '%'
                          ) > 0
                    ORDER BY times_asked DESC
                """)
                question_stats = []
                for row in cursor.fetchall():
                    question_stats.append({
                        'question_id': row[0],
                        'question_text': row[1],
                        'difficulty_level': row[2],
                        'times_asked': row[3],
                        'yes_count': row[4],
                        'no_count': row[5],
                        'dont_know_count': row[6],
                        'probably_count': row[7]
                    })

                admin_stats = {
                    'system_stats': system_stats,
                    'triangle_stats': triangle_stats,
                    'question_stats': question_stats,
                    'theorems': theorems,
                    'questions': questions
                }

            return render_template('User_Profile_Page.html',
                               user=user,
                               user_stats=user_stats,
                               recent_activity=recent_activity,
                               admin_stats=admin_stats)

    except Exception as e:
        print(f"Error in profile route: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('login_page.login'))