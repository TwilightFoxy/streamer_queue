from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    queues = db.relationship('Queue', backref='creator', lazy=True)

class Queue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entries = db.relationship('QueueEntry', backref='queue', lazy=True)

    def __repr__(self):
        return f'<Queue {self.name}>'

class QueueEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='waiting')
    content = db.Column(db.Text, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('queue.id'), nullable=False)

class ContentOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

