# Login_Page.py
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from db_utils import verify_user
from UserLogger import UserLogger

login_page = Blueprint('login_page', __name__,
                       template_folder='templates',
                       static_folder='static')


@login_page.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            # Check if all fields are filled
            if not all([email, password]):
                return jsonify({
                    'success': False,
                    'error': 'נא למלא את כל השדות'
                })

            # Verify user credentials
            user = verify_user(email, password)
            if user:
                session['user'] = user
                UserLogger.log_login(True, email)
                return jsonify({'success': True})
            else:
                UserLogger.log_login(False, email, 'Invalid credentials')
                return jsonify({
                    'success': False,
                    'error': 'אימייל או סיסמה שגויים'
                })

        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה בעת ההתחברות. אנא נסה שנית מאוחר יותר'
            }), 500

    return render_template('Login_Page.html')


@login_page.route('/logout')
def logout():
    UserLogger.log_logout()
    session.pop('user', None)
    return redirect(url_for('home_page.home'))