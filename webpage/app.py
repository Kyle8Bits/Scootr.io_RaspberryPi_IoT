from flask import Flask, render_template, redirect, url_for, request, session
from routes.booking_routes import booking_bp
from routes.user_routes import user_bp  
from routes.profile_routes import profile_bp
from routes.report_routes import report_bp
from routes.admin_routes import admin_bp
from routes.engineer_routes import engineer_bp
from routes.chatbot_routes import chatbot_bp
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from utils.session_utils import mail
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'


load_dotenv()  # Load .env into environment

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['GOOGLE_MAPS_API_KEY'] = os.getenv("GOOGLE_MAPS_API_KEY")

# mail = Mail()


# ------------------ BLUEPRINT REGISTRATION ------------------

app.register_blueprint(user_bp)       
app.register_blueprint(booking_bp)    
app.register_blueprint(profile_bp)
app.register_blueprint(report_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(engineer_bp)
app.register_blueprint(chatbot_bp)

# ------------------ PUBLIC ROUTES ------------------

@app.route('/')
def landing():
    return render_template('landing.html')

# ------------------ OTHER ROUTES ------------------

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('user.login'))  
    return render_template('history.html')

# ------------------ ERROR HANDLING ------------------
@app.errorhandler(Exception)
def handle_unexpected_error(e):
    print(f"Unexpected Error: {e}")
    return render_template("errors/500.html"), 500

@app.errorhandler(404)
def handle_404(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def handle_500(e):
    return render_template("errors/500.html"), 500

# ------------------ MAIN ------------------

if __name__ == "__main__":
    mail.init_app(app)
    app.run(host='0.0.0.0', port=5001, debug=True)