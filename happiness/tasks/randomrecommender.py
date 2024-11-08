'''A random recommender for tasks'''
import random
from typing import List

from happiness.tasks.recommender import TaskRecommenderInterface
from happiness.tasks.task import TaskWrapper


class RandomRecommender(TaskRecommenderInterface):
    '''Random Recommender'''
    def recommend_tasks(self, tasks: List[TaskWrapper], num_tasks: int) -> List[TaskWrapper]:
        '''Recommend random tasks'''
        return random.sample(tasks, num_tasks)