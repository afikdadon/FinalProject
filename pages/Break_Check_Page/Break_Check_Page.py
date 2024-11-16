from flask import Blueprint, render_template

Break_Check_Page_bp = Blueprint(
    'Break_Check_Page',
    __name__,
    static_folder='static',
    static_url_path='/Break_Check_Page/static',
    template_folder='templates'
)

@Break_Check_Page_bp.route('/Break_Check_Page')
def Break_Check_Page():
    return render_template('Break_Check_Page.html')