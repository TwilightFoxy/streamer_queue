from app import create_app, db
from app.models import ContentOption

app = create_app()

def seed_content_options():
    options = ["Бездна", "Театр", "Обзор"]
    for option in options:
        if not ContentOption.query.filter_by(name=option).first():
            db.session.add(ContentOption(name=option))
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        seed_content_options()  # Добавляем варианты Content
    app.run(debug=True)