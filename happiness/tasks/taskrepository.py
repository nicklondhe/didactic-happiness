'''Task Repository'''
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session

from happiness.tasks.model import Recommendation, Task
from happiness.tasks.randomrecommender import RandomRecommender
from happiness.tasks.task import TaskWrapper

class TaskRepository:
    '''Task Repository'''
    def __init__(self, db_session: Session):
        '''Initialize task repository'''
        self._db_session = db_session
        self._recommender = RandomRecommender()

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
        tasks = self._db_session.query(Task).filter_by(status='pending').all()
        return [TaskWrapper(task) for task in tasks]

    def recommend_tasks(self, num_tasks: int) -> List[TaskWrapper]:
        '''Recommend tasks based on user's mood'''
        tasks = self.get_tasks()
        recommendations = self._recommender.recommend_tasks(tasks, num_tasks)
        self.save_recommendations(recommendations)
        return recommendations

    def save_recommendations(self, tasks: List[TaskWrapper]) -> None:
        '''Save recommended tasks'''
        curr_ts = datetime.now(timezone.utc)
        recommendations = [Recommendation(
            task_id=task.get_id(),
            rec_ts=curr_ts
            ) for task in tasks]
        self._db_session.add_all(recommendations)
        self._db_session.commit()
