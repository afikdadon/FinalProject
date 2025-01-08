from flask import Blueprint, render_template, session

home_page = Blueprint('home_page', __name__,
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='/Home_Page/static')


@home_page.route('/')
def home():
    # Get user data from session if logged in
    user = session.get('user', None)
    user_name = user['first_name'] if user else None
    is_logged_in = user is not None

    return render_template('Home_Page.html',
                           user_name=user_name,
                           is_logged_in=is_logged_in)