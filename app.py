"""
app.py - DigiLib production entry point
  Local:      python app.py
  Production: gunicorn app:application
"""
import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, Admin, Shift, Seat


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # Extensions
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view         = 'main.admin_login'
    login_manager.login_message      = 'Please login to access the admin panel.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(uid):
        return Admin.query.get(int(uid))

    # Blueprint
    from routes import main
    app.register_blueprint(main)

    # DB + seed
    with app.app_context():
        db.create_all()
        _seed()

    return app


def _seed():
    """Create default admin, shifts and seats if not present"""
    from config import Config
    if not Admin.query.first():
        a = Admin(username=Config.ADMIN_USERNAME)
        a.set_password(Config.ADMIN_PASSWORD)
        db.session.add(a)
        print(f"Admin created → {Config.ADMIN_USERNAME} / {Config.ADMIN_PASSWORD}")

    if not Shift.query.first():
        for num, name, s, e in [(1,'1st Shift','6:00 AM','11:00 AM'),
                                 (2,'2nd Shift','11:00 AM','4:00 PM'),
                                 (3,'3rd Shift','4:00 PM','9:00 PM')]:
            db.session.add(Shift(shift_number=num, name=name, start_time=s, end_time=e))

    if not Seat.query.first():
        for i in range(1, 93):
            db.session.add(Seat(seat_number=i))

    db.session.commit()


# Gunicorn uses this
application = create_app()

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"""
  ╔══════════════════════════════════════════╗
  ║ SHIVA INFOTECH DIGITAL LIBRARY          ║
  ╠══════════════════════════════════════════╣
  ║  Local:   http://127.0.0.1:{port}         ║
  ║  Admin:   /admin/login                  ║
  ║  User:    {Config.ADMIN_USERNAME:<10}               ║
  ║  Pass:    {Config.ADMIN_PASSWORD:<10}               ║
  ╚══════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG','0')=='1')
