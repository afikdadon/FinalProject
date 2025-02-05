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
    return render_template('Contact_Page.html', user=user)


@contact_page.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')

            # Validate required fields
            if not all([name, email, subject, message]):
                flash('כל השדות הם חובה', 'error')
                return redirect(url_for('contact_page.contact'))

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ContactMessages (name, email, subject, message)
                    VALUES (?, ?, ?, ?)
                """, (name, email, subject, message))
                conn.commit()
                flash('ההודעה נשלחה בהצלחה!', 'success')
        except Exception as e:
            print(f"Error saving message: {e}")
            flash('אירעה שגיאה בשליחת ההודעה. אנא נסה שוב.', 'error')

        return redirect(url_for('home_page.home'))