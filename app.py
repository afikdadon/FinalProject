from flask import Flask
import os

app = Flask(__name__)

# from pages.Home_Page.Home_Page import Home_Page_bp
# app.register_blueprint(Home_Page_bp)

from pages.Break_Check_Page.Break_Check_Page import Break_Check_Page_bp
app.register_blueprint(Break_Check_Page_bp, url_prefix='/Break_Check_Page')

from pages.Login_Page.Login_Page import login_page
app.register_blueprint(login_page, url_prefix='/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
