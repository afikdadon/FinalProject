from flask import Blueprint, render_template, request, redirect, url_for, flash

# Create Blueprint
login_page = Blueprint('login_page', __name__,
                      template_folder='templates',
                      static_folder='static')

@login_page.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # For demonstration, just redirect to home
        return redirect(url_for('home_page.home'))
    return render_template('Login_Page.html')