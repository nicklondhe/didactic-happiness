'''Helper to query data for reports'''
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

import pandas as pd

from happiness.tasks.model import WorkLog


class ReportsHelper:
    '''Class to query data for reports'''
    def __init__(self, db_session: Session):
        '''Init'''
        self._db_session = db_session

    def _get_worklogs(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        '''Query worklogs between the two dates'''
        worklogs = self._db_session.query(WorkLog).filter(
            func.strftime('%s', WorkLog.start_ts) >= str(int(start_date.timestamp())),
            func.strftime('%s', WorkLog.end_ts) < str(int(end_date.timestamp()))
        ).all()
        data = [{
            'start_ts': worklog.start_ts,
            'end_ts': worklog.end_ts,
        } for worklog in worklogs]
        df = pd.DataFrame(data)

        df['seconds_worked'] = (df['end_ts'] - df['start_ts']).dt.total_seconds()
        df = df[df['seconds_worked'] <= (3 * 3600)]
        return df

    def get_avg_task_time(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        '''Get avg time spent on tasks between the two given dates'''
        df = self._get_worklogs(start_date, end_date)
        df['day_of_week'] = df['start_ts'].dt.dayofweek
        df['hour_of_day'] = df['start_ts'].dt.hour
        df['minutes_worked'] = df['seconds_worked'] / 60
        grouped = df.groupby(['day_of_week', 'hour_of_day'])['minutes_worked'].mean().reset_index()
        return grouped

