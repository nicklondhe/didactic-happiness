'''Task Repository'''
from typing import List
from sqlalchemy.orm import Session

from happiness.tasks.model import Task
from happiness.tasks.task import TaskWrapper

class TaskRepository:
    '''Task Repository'''
    def __init__(self, db_session: Session):
        '''Initialize task repository'''
        self._db_session = db_session
        #self._recommender = recommender

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

'''
    def recommend_tasks(self, num_tasks: int) -> List[TaskWrapper]:
        tasks = self.get_tasks()
        return self._recommender.recommend_tasks(tasks, num_tasks)
'''
