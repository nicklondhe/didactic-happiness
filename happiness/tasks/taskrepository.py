'''Task Repository'''
from datetime import datetime, timedelta, timezone
from typing import List

from loguru import logger
from sqlalchemy import and_, not_, func, text
from sqlalchemy.orm import Session
import pandas as pd

from happiness import MODEL_DIR
from happiness.tasks.model import Recommendation, Task, TaskSummary, WorkLog
from happiness.tasks.mabrecommender import MABRecommender
from happiness.tasks.task import TaskWrapper

class TaskRepository:
    '''Task Repository'''
    def __init__(self, db_session: Session):
        '''Initialize task repository'''
        self._db_session = db_session
        #TODO: Fix hardcoded file name
        self._recommender = MABRecommender(mdl_file=f'{MODEL_DIR}/eps-cmab.pkl')

    def add_task(self, task: TaskWrapper) -> None:
        '''Add a new task'''
        new_task = Task(
            name=task.get_name(),
            complexity=task.get_complexity(),
            type=task.get_type(),
            priority=task.get_priority(),
            repeatable=task.is_repeatable()
        )
        self._db_session.add(new_task)
        self._db_session.commit()

    def get_tasks(self) -> List[TaskWrapper]:
        '''Get all pending tasks'''
        tasks = self._db_session.query(Task).filter(not_(Task.status == 'done')).all()
        return [TaskWrapper(task) for task in tasks]

    def recommend_tasks(self, num_tasks: int) -> List[TaskWrapper]:
        '''Recommend tasks based on user's mood'''
        tasks = self.get_tasks()
        recommendations = self._recommender.recommend_tasks(tasks, num_tasks)
        self.save_recommendations(recommendations, num_tasks)
        return recommendations

    def save_recommendations(self, tasks: List[TaskWrapper], num_tasks: int) -> None:
        '''Save recommended tasks'''
        curr_ts = datetime.now(timezone.utc)
        recommendations = [Recommendation(
            task_id=task.get_id(),
            rec_ts=curr_ts
            ) for task in tasks]
        self._db_session.add_all(recommendations)
        self._db_session.commit()

        assert len(recommendations) == num_tasks, 'Recommendations not saved properly'

        for idx in range(num_tasks):
            logger.debug(f'Setting rec_id {recommendations[idx].id} for task {tasks[idx].get_id()}')
            tasks[idx].set_rec_id(recommendations[idx].id) #copy rec_id back to task

    def get_reschedulable_tasks(self) -> List[TaskWrapper]:
        '''Get repeatable tasks that have been completed'''
        tasks = self._db_session.query(Task).filter(
            and_(Task.repeatable == 1, Task.status == 'done')).all() # TODO: index?
        return [TaskWrapper(task) for task in tasks]

    def _update_task_status(self, task_id: int,
                            current_status: str, new_status: str,
                            clear_dt: bool = False) -> Task:
        '''Update task status'''
        task = self._db_session.query(Task).filter_by(id=task_id, status=current_status).first()
        if task is None:
            raise ValueError(f'Task with id {task_id} is not in {current_status} state')
        task.status = new_status

        if clear_dt:
            task.next_scheduled = None

        return task

    def _create_work_log(self, task_id: int, rec_id: int):
        '''Create work log'''
        logger.info(f'Creating a new work log for task {task_id} and recommendation {rec_id}')
        work_log = WorkLog(task_id=task_id, rec_id=rec_id, start_ts=datetime.now(timezone.utc))
        self._db_session.add(work_log)

    def _update_work_log(self, task_id: int, rec_id: int) -> WorkLog:
        '''Update work log'''
        work_log = self._db_session.query(WorkLog).filter_by(
            task_id=task_id, rec_id=rec_id, end_ts=None)\
            .order_by(WorkLog.start_ts.desc()).first()

        if work_log:
            work_log.end_ts = datetime.now(timezone.utc)

            if work_log.start_ts and work_log.start_ts.tzinfo is None:
                logger.debug('Updating worklog start timezone to UTC')
                work_log.start_ts = work_log.start_ts.replace(tzinfo=timezone.utc)
            return work_log
        else:
            msg = 'Could not find a work log for the given task' \
                  f' {task_id} and recommendation {rec_id}'
            raise ValueError(msg)

    def _update_task_summary(self, task_id: int, time_worked: int = 0,
                             has_end_date: bool = False, rating: int = None) -> TaskSummary:
        '''Update task summary'''
        logger.debug(f'Updating task summary for task {task_id}')
        task_summary = self._db_session.query(TaskSummary).filter_by(
            task_id=task_id, has_ended=0).first()
        if task_summary:
            task_summary.num_restarts += 1
            task_summary.time_worked += time_worked
            if has_end_date:
                task_summary.end_date = datetime.now(timezone.utc)
                task_summary.has_ended = True
            if rating is not None:
                task_summary.rating = rating
        else:
            task_summary = TaskSummary(
                task_id=task_id,
                start_date=datetime.now(timezone.utc)
            )
            self._db_session.add(task_summary)
        logger.debug(f'Task summary: {task_summary}')
        return task_summary

    def _find_recommendation(self, task_id: int) -> int:
        '''Find recommendation id'''
        worklog = self._db_session.query(WorkLog).filter_by(task_id=task_id, end_ts=None)\
            .order_by(WorkLog.start_ts.desc()).first()
        if worklog is None:
            raise ValueError(f'No active work log found for task {task_id}')
        return worklog.rec_id

    def _find_resched_tasks(self, tgt_date: datetime.date) -> List[int]:
        '''Find tasks that are to be rescheduled on the given date'''
        rows = self._db_session.query(Task).filter_by(next_scheduled=tgt_date, repeatable=1).all()
        return [row.id for row in rows] if rows else []

    def _stop_inprogress_tasks(self):
        '''Stop all tasks in progress'''
        tasks = self._db_session.query(Task.id, WorkLog.rec_id).join(
            WorkLog, Task.id == WorkLog.task_id
            ).filter(
                Task.status == 'in_progress',
                WorkLog.end_ts is None
                ).all()
        for task in tasks:
            self.stop_task(task[0], task[1])

    def start_task(self, task_id: int, rec_id: int) -> str:
        '''Start a task'''
        try:
            task = self._update_task_status(task_id, 'pending', 'in_progress')
            self._create_work_log(task_id, rec_id)
            self._update_task_summary(task_id)
            self._db_session.commit()
            self._recommender.update_chosen_task(task_id)
            return f'Task {task.name} started successfully!'
        except ValueError as err:
            logger.exception(err)
            return str(err)

    def stop_task(self, task_id: int, rec_id: int) -> str:
        '''Stop a task'''
        try:
            if rec_id == -1:
                rec_id = self._find_recommendation(task_id)

            task = self._update_task_status(task_id, 'in_progress', 'pending')
            work_log = self._update_work_log(task_id, rec_id)
            time_worked = (work_log.end_ts - work_log.start_ts).seconds
            self._update_task_summary(task_id, time_worked=time_worked)
            self._db_session.commit()
            return f'Task {task.name} stopped successfully!'
        except ValueError as err:
            logger.exception(err)
            return str(err)

    def finish_task(self, task_id: int, rec_id: int, rating: int = 1) -> str:
        '''Finish a task'''
        try:
            if rec_id == -1:
                rec_id = self._find_recommendation(task_id)

            task = self._update_task_status(task_id, 'in_progress', 'done')
            work_log = self._update_work_log(task_id, rec_id)
            time_worked = (work_log.end_ts - work_log.start_ts).seconds
            self._update_task_summary(task_id, time_worked=time_worked,
                                      has_end_date=True, rating=rating)

            # auto-schedule
            if task.repeatable:
                next_date = self._find_next_schedule_date(task_id)
                if next_date:
                    task.next_scheduled = next_date

            self._db_session.commit()
            return f'Task {task.name} finished successfully!'
        except ValueError as err:
            logger.exception(err)
            return str(err)

    def start_day(self):
        '''Day start'''
        self._recommender.load()

    def end_day(self):
        '''Day end'''
        self._recommender.save()
        self._stop_inprogress_tasks()

    def reschedule_tasks(self, task_ids: List[int], auto: bool = False) -> str:
        '''Reschedule tasks with given ids'''
        tasks = []
        message = None
        if not task_ids:
            return 'No tasks rescheduled'

        try:
            for task_id in task_ids:
                task = self._update_task_status(task_id, 'done', 'pending', True)
                tasks.append(task)
        except ValueError as err:
            logger.exception(err)
            message = str(err)

        if not message:
            self._db_session.commit()
            task_names = [task.name for task in tasks]
            auto_prefix = 'automatically ' if auto else ''
            message = f'Tasks {task_names} {auto_prefix} rescheduled succesfully!'
        return message

    def get_worklog_summary(self, start_date: datetime, end_date: datetime) -> dict:
        '''Get a worklog summary between the two given dates'''
        #query worklog - use tz aware dates directly
        worklogs = self._db_session.query(WorkLog, Task).filter(
            WorkLog.start_ts >= start_date,
            WorkLog.end_ts < end_date
        ).filter(WorkLog.task_id == Task.id).all()
        data = [{
            'start_ts': worklog[0].start_ts.astimezone(start_date.tzinfo),
            'end_ts': worklog[0].end_ts.astimezone(start_date.tzinfo),
            'type': worklog[1].type
        } for worklog in worklogs]
        df = pd.DataFrame(data)

        # group by + sum
        df['hours_worked'] = (df['end_ts'] - df['start_ts']).dt.total_seconds() / 3600
        df['start_date'] = df['start_ts'].dt.date
        # data filtering
        df = df[df['hours_worked'] <= 3]

        summary = df.groupby(['start_date', 'type'])['hours_worked'].sum().to_dict()
        return summary

    def get_task_completion_summary(self, start_date: datetime, end_date: datetime) -> list:
        '''Get task completions by day of week + hour of day between given date range'''
        # Query for heatmap data
        heatmap_data = (
            self._db_session.query(TaskSummary.end_date)
            .filter(
                TaskSummary.has_ended == 1,
                TaskSummary.end_date >= start_date,
                TaskSummary.end_date < end_date
            )
            .all()
        )

        # convert timestamps
        local_tz = start_date.tzinfo
        converted_data = [
            row[0].astimezone(local_tz)  # Directly convert to local timezone
            for row in heatmap_data
        ]

        # Aggregate tasks by day of week and hour
        data_list = [{"day_of_week": dt.weekday(), "hour_of_day": dt.hour} for dt in converted_data]
        return data_list

    def get_worklog_splits(self, start_date: datetime, end_date: datetime) -> list:
        '''Get worklog splits by complexity and priority'''
        subquery = self._db_session.query(
            WorkLog.task_id,
            (
                func.strftime('%s', WorkLog.end_ts) - func.strftime('%s', WorkLog.start_ts)
            ).label('time_worked')
        ).filter(
            WorkLog.start_ts >= start_date,
            WorkLog.end_ts < end_date
        ).subquery()

        data = self._db_session.query(
            Task.priority, Task.complexity,
            func.sum(subquery.c.time_worked).label('total_time')
        ).join(
            Task, Task.id == subquery.c.task_id
        ).group_by(
            Task.priority, Task.complexity
        ).all()
        return data

    def _find_next_schedule_date(self, task_id: int) -> datetime.date:
        '''Find next auto schedule date for given task'''
        query = f'''
            SELECT avg(interval_days) as avg_interval
            FROM (
                WITH task_intervals AS (
                    SELECT
                        ts.task_id,
                        ts.start_date,
                        LEAD(ts.start_date) OVER (PARTITION BY ts.task_id ORDER BY ts.start_date) AS next_start_date,
                        ROW_NUMBER() OVER (PARTITION BY ts.task_id ORDER BY ts.start_date DESC) AS rn
                    FROM
                        task_summary ts
                    JOIN task t ON ts.task_id = t.id
                    WHERE t.repeatable = 1
                    AND t.id = {task_id}
                )
                SELECT
                    task_id,
                    julianday(next_start_date) - julianday(start_date) AS interval_days
                FROM
                    task_intervals
                WHERE
                    next_start_date IS NOT NULL
                    AND rn <= 10
            )
        '''
        result = self._db_session.execute(text(query)).scalar_one_or_none()
        next_date = None
        if result:
            interval = round(result)
            next_date = datetime.now(timezone.utc) + timedelta(days=interval)
            next_date = next_date.date()
            logger.info(f'Setting next scheduled date {next_date} for task id {task_id}')

        return next_date

    def auto_reschedule(self, tgt_date: datetime.date = None) -> str:
        '''Automatically reschedule tasks due on given target date'''
        if tgt_date is None:
            tgt_date = datetime.now(timezone.utc).date()

        task_ids = self._find_resched_tasks(tgt_date)
        return self.reschedule_tasks(task_ids, True)
