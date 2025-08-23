from app import app
from freelancer_models import db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ All tables created (users, clients, projects).")



