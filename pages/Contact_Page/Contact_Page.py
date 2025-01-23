from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db_utils import get_db_connection

contact_page = Blueprint('contact_page', __name__,
                        template_folder='templates',
                        static_folder='static',
                        static_url_path='/contact/static')


@contact_page.route('/')
def contact():
    session.pop('_flashes', None)
    user = session.get('user', None)
    if not user:
        return redirect(url_for('login_page.login'))
    return render_template('Contact_Page.html', user=user)


@contact_page.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        user = session.get('user', None)
        if not user:
            return redirect(url_for('login_page.login'))

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ContactMessages (user_id, name, email, subject, message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user['user_id'],
                    request.form.get('name'),
                    request.form.get('email'),
                    request.form.get('subject'),
                    request.form.get('message')
                ))
                conn.commit()
                flash('ההודעה נשלחה בהצלחה!', 'success')
        except Exception as e:
            print(f"Error saving message: {e}")
            flash('אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.', 'error')

        return redirect(url_for('home_page.home'))