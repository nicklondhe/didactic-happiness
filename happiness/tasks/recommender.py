'''Task Recommender Interface'''
from abc import ABC, abstractmethod
from typing import List

from happiness.tasks.task import TaskWrapper

class TaskRecommenderInterface(ABC):
    '''Task Recommender Interface'''
    @abstractmethod
    def recommend_tasks(self, tasks: List[TaskWrapper], num_tasks: int) -> List[TaskWrapper]:
        '''Recommend tasks based on user's mood'''
