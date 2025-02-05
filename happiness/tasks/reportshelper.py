'''Helper to query data for reports'''
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.orm import Session

import pandas as pd

from happiness.tasks.model import WorkLog


class ReportsHelper:
    '''Class to query data for reports'''
    def __init__(self, db_session: Session):
        '''Init'''
        self._db_session = db_session

    def _get_worklogs(self, start_ts: int, end_ts: int) -> pd.DataFrame:
        '''Query worklogs between the two dates'''
        worklogs = self._db_session.query(WorkLog).filter(
            func.strftime('%s', WorkLog.start_ts) >= str(start_ts),
            func.strftime('%s', WorkLog.end_ts) < str(end_ts)
        ).all()
        data = [{
            'start_ts': worklog.start_ts,
            'end_ts': worklog.end_ts,
        } for worklog in worklogs]
        df = pd.DataFrame(data)

        df['seconds_worked'] = (df['end_ts'] - df['start_ts']).dt.total_seconds()
        df = df[df['seconds_worked'] <= (3 * 3600)]
        return df

    def _get_task_switch_count(self, start_ts: int, end_ts: int) -> pd.DataFrame:
        '''Count task switches by day'''
        query = f'''
            WITH OrderedTasks AS (
                SELECT 
                    task_id,
                    start_ts,
                    end_ts,
                    DATE(start_ts) AS task_date,
                    LAG(task_id) OVER (PARTITION BY DATE(start_ts) ORDER BY start_ts) AS prev_task
                FROM work_log
                where strftime('%s', start_ts) >= '{start_ts}' and strftime('%s', end_ts) < '{end_ts}'
            )
            SELECT 
                task_date,
                COUNT(*) AS task_switches
            FROM OrderedTasks
            WHERE task_id <> prev_task  -- Only count when task_id changes
            GROUP BY task_date
            ORDER BY task_date
        '''
        result = self._db_session.execute(text(query)).all()
        return pd.DataFrame(result)

    def _get_avg_task_time(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        '''Get avg time spent on tasks between the two given dates'''
        df = self._get_worklogs(start_date, end_date)
        df['task_date'] = df['start_ts'].dt.date
        df['minutes_worked'] = df['seconds_worked'] / 60
        grouped = df.groupby(['task_date'])['minutes_worked'].mean().reset_index()
        return grouped

    def get_focus_summary(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        '''Summarize focus by day as avg time worked per task and number of task switches'''
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        df_switches = self._get_task_switch_count(start_ts, end_ts)
        df_avg = self._get_avg_task_time(start_ts, end_ts)
        df_avg['task_date'] = pd.to_datetime(df_avg['task_date'])
        df_switches['task_date'] = pd.to_datetime(df_switches['task_date'])
        df_merged = df_switches.merge(df_avg, on='task_date')
        return df_merged.fillna(0)
