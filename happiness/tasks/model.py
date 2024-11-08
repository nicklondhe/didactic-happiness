'''Task db model'''
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
    status = db.Column(db.String(10), nullable=False, default='todo')
