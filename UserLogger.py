import json
from datetime import datetime
from flask import session
from db_utils import get_db_connection


class UserLogger:
    @staticmethod
    def log_action(action_type, action_data):
        try:
            user_id = session.get('user', {}).get('user_id')

            # Convert action_data to JSON string if it's a dict
            if isinstance(action_data, dict):
                action_data = json.dumps(action_data)

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO UserLogs (user_id, action_type, action_data)
                    VALUES (?, ?, ?)
                """, (user_id, action_type, action_data))
                conn.commit()

        except Exception as e:
            print(f"Logging error: {str(e)}")
            # Don't raise the exception - logging should never break the main application flow

    @staticmethod
    def log_login(success, email, error_message=None):
        data = {
            'email': email,
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('LOGIN_ATTEMPT', data)

    @staticmethod
    def log_registration(success, email, error_message=None):
        data = {
            'email': email,
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('REGISTRATION', data)

    @staticmethod
    def log_question_answer(question_id, question_text, answer):
        data = {
            'question_id': question_id,
            'question_text': question_text,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('QUESTION_ANSWER', data)

    @staticmethod
    def log_session_start(session_type):
        data = {
            'session_type': session_type,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('SESSION_START', data)

    @staticmethod
    def log_session_end(session_type, final_theorem_id=None):
        data = {
            'session_type': session_type,
            'final_theorem_id': final_theorem_id,
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('SESSION_END', data)

    @staticmethod
    def log_profile_view():
        data = {
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('PROFILE_VIEW', data)

    @staticmethod
    def log_logout():
        data = {
            'timestamp': datetime.now().isoformat()
        }
        UserLogger.log_action('LOGOUT', data)

    @staticmethod
    def log_feedback_submission():
        data = {
            "timestamp": datetime.now().isoformat(),
            "action": "FEEDBACK_SUBMISSION"
        }
        UserLogger.log_action('FEEDBACK_SUBMISSION', data)