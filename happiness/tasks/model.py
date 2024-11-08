'''Task db model'''
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Task(db.Model):
    '''Task model'''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    complexity = db.Column(db.String(10), nullable=False, default='simple')
    type = db.Column(db.String(20))
    due_date = db.Column(db.String(10))
    priority = db.Column(db.String(10), nullable=False, default='low')
    repeatable = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(10), nullable=False, default='pending') #TODO: needs an index


class Recommendation(db.Model):
    '''Recommendation model'''
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    rec_ts = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    task = db.relationship('Task', backref='recommendations')
