'''A MAB based recommender for tasks'''
from collections import defaultdict
from typing import Dict, List
import pickle
import random

from loguru import logger
from happiness.tasks.recommender import TaskRecommenderInterface
from happiness.tasks.task import TaskWrapper


class MABRecommender(TaskRecommenderInterface):
    '''MAB Recommender'''
    def __init__(self, mdl_file: str, epsilon: float = 0.2):
        '''Initialize MAB recommender'''
        self.mdl_file = mdl_file
        self.qvalues, self.counts = self._load_model(self.mdl_file)
        self.epsilon = epsilon
        self.last_tasks = {} # last recs
        self.task_chosen = False
        logger.info(f'Loaded MAB recommender with epsilon \
                    {self.epsilon} and {len(self.qvalues)} arms')

    def _load_model(self, mdl_file: str) -> dict:
        '''Load model from a pickle file'''
        data = {'qvalues': {}, 'counts': {}}

        with open(mdl_file, 'rb') as f:
            data = pickle.load(f)

        return data['qvalues'], data['counts']

    def recommend_tasks(self, tasks: List[TaskWrapper], num_tasks: int) -> List[TaskWrapper]:
        '''Recommend tasks based on MAB'''
        if not self.task_chosen: # nothing from last set
            self.update_qvalues()

        hashed_tasks = self._as_hashed_tasks(tasks)
        recs = []
        arm_keys = set(hashed_tasks.keys())
        arm_history = set()
        qvalues = sorted((qv for qv in self.qvalues.items() if qv[0] in arm_keys),
                         key = lambda x: x[1], reverse=True)
        for k in arm_keys:
            if k not in qvalues:
                qvalues.append((k, 0))

        while len(recs) < num_tasks:
            if random.random() < self.epsilon:
                available_arms = list(arm_keys - arm_history)
                selected_arm = random.choice(available_arms)
            else:
                for arm, _ in qvalues:
                    if arm not in arm_history:
                        selected_arm = arm
                        break
            task = hashed_tasks[selected_arm][0]
            recs.append(task)
            arm_history.add(selected_arm)
            self.last_tasks[task.get_id()] = task.get_hash_code()
        return recs

    def _as_hashed_tasks(self, tasks: List[TaskWrapper]) -> Dict[int, List[TaskWrapper]]:
        '''Convert tasks into a dict with hash as key and tasks as list'''
        random.shuffle(tasks)
        hashed_tasks = defaultdict(list)
        for task in tasks:
            hashed_tasks[task.get_hash_code()].append(task)
        return hashed_tasks

    def update_chosen_task(self, task_id: int) -> None:
        self.task_chosen = True
        self.update_qvalues(task_id)
        return super().update_chosen_task(task_id)

    def update_qvalues(self, task_id: int = None) -> None:
        '''Set reward as 1 for selected task id, and 0 for others'''
        for t_id, t_hash in self.last_tasks.items():
            count = self.counts.get(t_hash, 0)
            count += 1
            reward = 1 if t_id == task_id else 0
            self.qvalues[t_hash] += (reward - self.qvalues[t_hash]) * 1.0 / count
            self.counts[t_hash] = count

    def load(self):
        '''Reload model'''
        self.qvalues, self.counts = self._load_model(self.mdl_file)

    def save(self):
        '''Save updated values'''
        with open(self.mdl_file, 'wb') as f:
            obj = {'qvalues': self.qvalues, 'counts': self.counts}
            pickle.dump(obj, f)
        return super().save()
