from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from db_utils import create_user
from extensions import bcrypt
from UserLogger import UserLogger
import re

registration_page = Blueprint('registration_page', __name__,
                            template_folder='templates',
                            static_folder='static')

def validate_input(first_name, last_name, email, password):
    name_pattern = r'^[\u0590-\u05FFa-zA-Z\s]+$'
    email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

    if not re.match(name_pattern, first_name):
        return False, 'שם פרטי חייב להכיל אותיות בלבד'

    if not re.match(name_pattern, last_name):
        return False, 'שם משפחה חייב להכיל אותיות בלבד'

    if not re.match(email_pattern, email):
        return False, 'כתובת אימייל לא תקינה'

    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(
            r'\d', password):
        return False, 'הסיסמה חייבת להכיל לפחות 8 תווים, אות גדולה, אות קטנה ומספר'

    return True, None

@registration_page.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Check if all fields are filled
            if not all([first_name, last_name, email, password, confirm_password]):
                return jsonify({
                    'success': False,
                    'error': 'נא למלא את כל השדות'
                })

            # Check if passwords match
            if password != confirm_password:
                return jsonify({
                    'success': False,
                    'error': 'הסיסמאות אינן תואמות'
                })

            # Validate input
            is_valid, error_message = validate_input(first_name, last_name, email, password)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': error_message
                })

            # Use the hash_password function from db_utils
            from db_utils import hash_password
            hashed_password = hash_password(password)

            # Try to create user
            if create_user(first_name, last_name, email, hashed_password):
                UserLogger.log_registration(True, email)
                return jsonify({'success': True})
            else:
                UserLogger.log_registration(False, email, 'Email already exists')
                return jsonify({
                    'success': False,
                    'error': 'כתובת האימייל שהזנת כבר קיימת במערכת'
                })

        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'אירעה שגיאה בעת יצירת המשתמש. אנא נסה שנית מאוחר יותר'
            }), 500

    return render_template('Registration_Page.html')