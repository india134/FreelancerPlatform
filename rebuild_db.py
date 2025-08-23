# rebuild_db.py

from freelancer_models import db
from app import create_app

app = create_app()

with app.app_context():
    # WARNING: this will DROP *ALL* your tables!
    db.drop_all()
    print("▶ Dropped all tables.")
    db.create_all()
    print("▶ Recreated all tables from your models.")
