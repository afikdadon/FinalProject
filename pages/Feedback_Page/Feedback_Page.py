from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from db_utils import get_db_connection
from UserLogger import UserLogger

feedback_page = Blueprint('feedback_page', __name__,
                          template_folder='templates',
                          static_folder='static')


@feedback_page.route('/')
def feedback():
    user = session.get('user', None)
    print("User session at feedback page load:", user)  # Debug log
    if not user:
        print("No user found, redirecting to login")  # Debug log
        return redirect(url_for('login_page.login'))
    return render_template('Feedback_Page.html')


@feedback_page.route('/submit', methods=['POST'])
def submit_feedback():
    try:
        print("Full session contents:", dict(session))

        if 'user' not in session:
            print("No user in session during feedback submission")
            return jsonify({'success': False, 'error': 'User is not logged in'}), 401

        user = session.get('user')
        print("User data during feedback submission:", user)

        user_id = user.get('user_id')
        print(f"User ID for feedback: {user_id}")

        if not user_id:
            print("No user ID in session")
            return jsonify({'success': False, 'error': 'No user ID found'}), 401

        # Get the form data
        data = request.get_json()
        if not data:
            print("No feedback data received")
            return jsonify({'success': False, 'error': 'No feedback data received'}), 400

        print(f"Processing feedback for user ID: {user_id}")
        print("Form data received:", data)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert feedback into database
        query = """
            INSERT INTO UserFeedback (
                user_id, 
                usability_easy_to_use, usability_clear_questions,
                usability_clear_interface, usability_easy_navigation,
                educational_concepts, educational_theorems,
                educational_guidance, educational_learning,
                format_dont_know_helpful, format_sufficient_options,
                format_would_use_again,
                intelligence_understood_responses, intelligence_relevant_questions,
                missing_questions, unclear_questions,
                suggested_improvements, expected_questions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            user_id,
            data.get('usability_easy_to_use'),
            data.get('usability_clear_questions'),
            data.get('usability_clear_interface'),
            data.get('usability_easy_navigation'),
            data.get('educational_concepts'),
            data.get('educational_theorems'),
            data.get('educational_guidance'),
            data.get('educational_learning'),
            data.get('format_dont_know_helpful'),
            data.get('format_sufficient_options'),
            data.get('format_would_use_again'),
            data.get('intelligence_understood_responses'),
            data.get('intelligence_relevant_questions'),
            data.get('missing_questions', ''),
            data.get('unclear_questions', ''),
            data.get('suggested_improvements', ''),
            data.get('expected_questions', '')
        )

        cursor.execute(query, values)
        conn.commit()
        conn.close()

        # Log the feedback submission
        UserLogger.log_feedback_submission()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in submit_feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'אירעה שגיאה בשמירת המשוב. אנא נסה שוב או צור קשר עם התמיכה.'
        }), 500