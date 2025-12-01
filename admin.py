from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username="user1").first()

    if not user:
        print("No user1 found")
    else:
        user.is_admin = True
        db.session.commit()
        print("user1 is admin")
