'''Task Repository'''
from datetime import datetime, timezone
from typing import List
from sqlalchemy import not_
from sqlalchemy.orm import Session

from happiness import MODEL_DIR
from happiness.tasks.model import Recommendation, Task, TaskSummary, WorkLog
from happiness.tasks.randomrecommender import RandomRecommender
from happiness.tasks.task import TaskWrapper

class TaskRepository:
    '''Task Repository'''
    def __init__(self, db_session: Session):
        '''Initialize task repository'''
        self._db_session = db_session
        #TODO: Fix hardcoded file name
        self._recommender = RandomRecommender()
        #self._recommender = MABRecommender(mdl_file=f'{MODEL_DIR}/eps-mab.pkl')

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
            tasks[idx].set_rec_id(recommendations[idx].id) #copy rec_id back to task


    def _update_task_status(self, task_id: int, current_status: str, new_status: str) -> Task:
        '''Update task status'''
        task = self._db_session.query(Task).filter_by(id=task_id, status=current_status).first()
        if task is None:
            raise ValueError(f'Task with id {task_id} is not in {current_status} state')
        task.status = new_status
        return task

    def _update_work_log(self, task_id: int, rec_id: int, has_end_date: bool = False) -> WorkLog:
        '''Update work log'''
        work_log = self._db_session.query(WorkLog).filter_by(task_id=task_id, rec_id=rec_id)\
            .order_by(WorkLog.start_ts.desc()).first()
        if work_log is None:
            work_log = WorkLog(
                task_id=task_id,
                rec_id=rec_id
            )
            self._db_session.add(work_log)

        if work_log:
            if has_end_date:
                work_log.end_ts = datetime.now(timezone.utc)

            if work_log.start_ts and work_log.start_ts.tzinfo is None:
                work_log.start_ts = work_log.start_ts.replace(tzinfo=timezone.utc)
        return work_log

    def _update_task_summary(self, task_id: int, time_worked: int = 0,
                             has_end_date: bool = False, rating: int = None) -> TaskSummary:
        '''Update task summary'''
        task_summary = self._db_session.query(TaskSummary).filter_by(task_id=task_id).first()
        if task_summary:
            task_summary.num_restarts += 1
            task_summary.time_worked += time_worked
            if has_end_date:
                task_summary.end_date = datetime.now(timezone.utc)
            if rating is not None:
                task_summary.rating = rating
        else:
            task_summary = TaskSummary(
                task_id=task_id,
                start_date=datetime.now(timezone.utc)
            )
            self._db_session.add(task_summary)
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
            self._update_work_log(task_id, rec_id)
            self._update_task_summary(task_id)
            self._db_session.commit()
            self._recommender.update_chosen_task(task_id)
            return f'Task {task.name} started successfully!'
        except ValueError as err:
            return str(err)

    def stop_task(self, task_id: int, rec_id: int) -> str:
        '''Stop a task'''
        try:
            if rec_id == -1:
                rec_id = self._find_recommendation(task_id)

            task = self._update_task_status(task_id, 'in_progress', 'pending')
            work_log = self._update_work_log(task_id, rec_id, has_end_date=True)
            time_worked = (work_log.end_ts - work_log.start_ts).seconds
            self._update_task_summary(task_id, time_worked=time_worked)
            self._db_session.commit()
            return f'Task {task.name} stopped successfully!'
        except ValueError as err:
            return str(err)

    def finish_task(self, task_id: int, rec_id: int, rating: int = 1) -> str:
        '''Finish a task'''
        try:
            if rec_id == -1:
                rec_id = self._find_recommendation(task_id)

            task = self._update_task_status(task_id, 'in_progress', 'done')
            work_log = self._update_work_log(task_id, rec_id, has_end_date=True)
            time_worked = (work_log.end_ts - work_log.start_ts).seconds
            self._update_task_summary(task_id, time_worked=time_worked,
                                      has_end_date=True, rating=rating)
            self._db_session.commit()
            return f'Task {task.name} finished successfully!'
        except ValueError as err:
            return str(err)

    def shutdown(self):
        '''Cleanup or shutdown'''
        self._recommender.save()
