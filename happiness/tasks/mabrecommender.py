'''A MAB based recommender for tasks'''
from numpy.random import beta
from typing import Dict, List
import numpy as np
import random

from happiness.tasks.recommender import TaskRecommenderInterface
from happiness.tasks.task import TaskWrapper


class MABRecommender(TaskRecommenderInterface):
    '''MAB Recommender'''
    def __init__(self, n_arms=5):
        '''Initialize MAB recommender'''
        #TODO: Initialize alpha and beta values for each arm
        self.n_arms = n_arms
        self.alphas = [1.0] * n_arms
        self.betas = [1.0] * n_arms
        self.id_arm_map = {}

    def load_arm_values(self, tasks: List[TaskWrapper]) -> Dict[int, List[TaskWrapper]]:
        '''Load arm values'''
        arm_values = {}
        for task in tasks:
            arm_id = task.get_id() % len(self.alphas) #TODO: Use a hash function
            if arm_id not in arm_values:
                arm_values[arm_id] = []
            arm_values[arm_id].append(task)
            self.id_arm_map[task.get_id()] = arm_id
        return arm_values

    def recommend_tasks(self, tasks: List[TaskWrapper], num_tasks: int) -> List[TaskWrapper]:
        '''Recommend tasks based on MAB'''
        arm_values = self.load_arm_values(tasks)
        sampled_probs = [beta(self.alphas[arm], self.betas[arm]).sample().item() for arm in range(self.n_arms)]
        top_k_arms = np.argsort(sampled_probs)[-num_tasks:]
        return [random.sample(arm_values[arm_id], 1) for arm_id in top_k_arms]
    
    def update_chosen_task(self, task_id: int) -> None:
        return super().update_chosen_task(task_id)
    