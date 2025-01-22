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
    next_scheduled = db.Column(db.Date)


class Recommendation(db.Model):
    '''Recommendation model'''
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    rec_ts = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    task = db.relationship('Task', backref='recommendations')


class WorkLog(db.Model):
    '''Work log model'''
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    rec_id = db.Column(db.Integer, db.ForeignKey('recommendation.id'))
    start_ts = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    end_ts = db.Column(db.DateTime)
    task = db.relationship('Task', backref='worklogs')
    recommendation = db.relationship('Recommendation', backref='worklogs')

class TaskSummary(db.Model):
    '''Task summary model'''
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    time_worked = db.Column(db.Integer, nullable=False, default=0)
    num_restarts = db.Column(db.Integer, nullable=False, default=0)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime)
    rating = db.Column(db.Integer, nullable=False, default=1)
    has_ended = db.Column(db.Boolean, default=False)
    task = db.relationship('Task', backref='summary')
