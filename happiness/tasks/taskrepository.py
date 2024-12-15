'''Task Repository'''
from datetime import datetime, timezone
from typing import List

from loguru import logger
from sqlalchemy import and_, not_
from sqlalchemy.orm import Session

from happiness.tasks.model import Recommendation, Task, TaskSummary, WorkLog
from happiness.tasks.randomrecommender import RandomRecommender
from happiness.tasks.task import TaskWrapper

class TaskRepository:
    '''Task Repository'''
    def __init__(self, db_session: Session):
        '''Initialize task repository'''
        self._db_session = db_session
        self._recommender = RandomRecommender()
        logger.info(f'Init task repository with a {self._recommender.__class__} recommender')

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

    def _update_task_status(self, task_id: int, current_status: str, new_status: str) -> Task:
        '''Update task status'''
        task = self._db_session.query(Task).filter_by(id=task_id, status=current_status).first()
        if task is None:
            raise ValueError(f'Task with id {task_id} is not in {current_status} state')
        task.status = new_status
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

    def start_task(self, task_id: int, rec_id: int) -> str:
        '''Start a task'''
        try:
            task = self._update_task_status(task_id, 'pending', 'in_progress')
            self._create_work_log(task_id, rec_id)
            self._update_task_summary(task_id)
            self._db_session.commit()
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
            self._db_session.commit()
            return f'Task {task.name} finished successfully!'
        except ValueError as err:
            logger.exception(err)
            return str(err)

    def reschedule_tasks(self, task_ids: List[int]) -> str:
        '''Reschedule tasks with given ids'''
        tasks = []
        message = None
        try:
            for task_id in task_ids:
                task = self._update_task_status(task_id, 'done', 'pending')
                tasks.append(task)
        except ValueError as err:
            logger.exception(err)
            message = str(err)

        if not message:
            self._db_session.commit()
            task_names = [task.name for task in tasks]
            message = f'Tasks {task_names} rescheduled succesfully!'
        return message
