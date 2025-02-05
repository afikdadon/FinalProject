from flask import Blueprint, render_template, session, jsonify, request, redirect, url_for
from pages.Question_Page.Geometry_Manager import Geometry_Manager
from UserLogger import UserLogger


question_page = Blueprint('question_page', __name__,
                          template_folder='templates',
                          static_folder='static')


@question_page.before_request
def check_active_session():
    """Only reset if there's no active session"""
    if 'geometry_state' not in session:
        manager = Geometry_Manager()
        manager.reset_session()


@question_page.route('/')
def question():
    user = session.get('user', None)
    user_role = user.get('role', 'user') if user else 'user'
    is_logged_in = user is not None

    if not is_logged_in:
        return redirect(url_for('login_page.login'))

    try:
        manager = Geometry_Manager()
        # First reset any existing session state
        manager.reset_session()

        # Log session start
        UserLogger.log_session_start("NEW_SESSION")

        question_id, question_text, debug_info = manager.get_next_question(is_admin=(user_role == 'admin'))
        initial_theorems = manager.get_relevant_theorems()

        return render_template('Question_Page.html',
                             user_role=user_role,
                             question_id=question_id,
                             question_text=question_text,
                             debug_info=debug_info,
                             initial_theorems=initial_theorems)
    except Exception as e:
        print(f"Error in question route: {str(e)}")
        return redirect(url_for('login_page.login'))


@question_page.route('/answer', methods=['POST'])
def process_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')

    try:
        manager = Geometry_Manager()
        (manager.
         process_answer(question_id, answer))

        next_question_id, next_question_text, debug_info = manager.get_next_question(
            is_admin=(session.get('user', {}).get('role') == 'admin')
        )

        # Get question history
        questions_history = manager.get_questions_history()

        UserLogger.log_question_answer(question_id, next_question_text, answer)
        theorems = manager.get_relevant_theorems()
        formatted_theorems = [{
            'id': theorem[0],
            'text': theorem[1],
            'weight': theorem[2],
            'category': theorem[0] if len(theorem) < 4 else theorem[3]
        } for theorem in theorems]
        # Get triangle weights from session for all users
        triangle_weights = session['geometry_state']['triangle_weights']

        response_data = {
            'success': True,
            'nextQuestion': {
                'id': next_question_id,
                'text': next_question_text
            },
            'questionsHistory': questions_history,
            'theorems': formatted_theorems,
            'triangle_weights': triangle_weights
        }

        # Add debug info only for admin users
        if session.get('user', {}).get('role') == 'admin':
            response_data['debug'] = debug_info



        return jsonify(response_data)
    except Exception as e:
        print(f"Error in answer route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/finish', methods=['POST'])
def finish_session():
    try:
        data = request.get_json()
        status = data.get('status', 'unknown')

        # Get current user session
        user = session.get('user')
        if not user:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        # Log the session end with status
        UserLogger.log_session_end(status, None)

        # Clear geometry-specific session data
        session.pop('geometry_state', None)

        # Determine redirect URL based on status
        if status == 'partial':
            redirect_url = url_for('question_page.question')
        else:
            redirect_url = url_for('home_page.home')

        return jsonify({
            'success': True,
            'redirect': redirect_url
        })
    except Exception as e:
        print(f"Error in finish_session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@question_page.route('/cleanup', methods=['POST'])
def cleanup_session():
    try:
        # Preserve user authentication while cleaning up
        user_data = session.get('user')

        # Get the most relevant theorem before cleaning
        manager = Geometry_Manager()
        theorems = manager.get_relevant_theorems()
        final_theorem_id = theorems[0][0] if theorems else None

        # Clear specific session data
        for key in list(session.keys()):
            if key != 'user':  # Keep the user session data
                session.pop(key, None)

        # Restore user data
        if user_data:
            session['user'] = user_data
            session.modified = True

        # Log session end
        UserLogger.log_session_end("CLEANUP", final_theorem_id)

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in cleanup_session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@question_page.route('/check-timeout', methods=['GET'])
def check_timeout():
    try:
        print("Received timeout check request")
        manager = Geometry_Manager()
        is_timeout = manager.check_timeout()
        print(f"Timeout check result: {is_timeout}")
        return jsonify({'timeout': is_timeout})
    except Exception as e:
        print(f"Error in check_timeout route: {str(e)}")
        return jsonify({'timeout': False, 'error': str(e)}), 500
