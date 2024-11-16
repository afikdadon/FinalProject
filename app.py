from flask import Flask

app = Flask(__name__)

# from pages.Home_Page.Home_Page import Home_Page_bp
# app.register_blueprint(Home_Page_bp)

from pages.Break_Check_Page.Break_Check_Page import Break_Check_Page_bp
app.register_blueprint(Break_Check_Page_bp)

if __name__ == '__main__':
    app.run(debug=True)
