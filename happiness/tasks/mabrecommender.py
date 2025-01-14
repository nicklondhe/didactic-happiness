'''A MAB based recommender for tasks'''
from collections import defaultdict
from datetime import datetime, timezone
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
        self.last_context = None
        self.last_tasks = {} # last recs
        self.task_chosen = False
        self.ce = ContextEncoder(6, 22, 4) #TODO: load from config?
        logger.info(f'Loaded MAB recommender with epsilon \
                    {self.epsilon} and {len(self.qvalues)} arms')

    def _load_model(self, mdl_file: str) -> dict:
        '''Load model from a pickle file'''
        data = {'qvalues': {}, 'counts': {}}

        with open(mdl_file, 'rb') as f:
            data = pickle.load(f)

        return data['qvalues'], data['counts']

    def _load_contextual_values(self) -> dict:
        '''Load contextual model based on time of day'''
        curr_hr = datetime.now(timezone.utc).hour
        ctx = self.ce.get_context(curr_hr)
        self.last_context = ctx
        ctx_qvalues = self.qvalues.get(ctx, None)
        if not ctx_qvalues:
            logger.error(f'Could not laod contextual values for {curr_hr}')
            self.last_context = None
        return ctx_qvalues

    def _as_hashed_tasks(self, tasks: List[TaskWrapper]) -> Dict[int, List[TaskWrapper]]:
        '''Convert tasks into a dict with hash as key and tasks as list'''
        random.shuffle(tasks)
        hashed_tasks = defaultdict(list)
        for task in tasks:
            hashed_tasks[task.get_hash_code()].append(task)
        return hashed_tasks

    @staticmethod
    def _sort_and_augment_qvalues(qvalues: dict, task_keys: set) -> list:
        '''Sort qvalues and augment with missing keys if any'''
        missing_keys = task_keys - qvalues.keys()
        sorted_qvalues = sorted((qv for qv in qvalues.items() if qv[0] in task_keys),
                         key = lambda x: x[1], reverse=True)
        for k in missing_keys:
            sorted_qvalues.append((k, 0))
        return sorted_qvalues

    def _run_mab(self, qvalues: Dict[int, float],
                 hashed_tasks: Dict[int, List[TaskWrapper]],
                 num_tasks: int) -> list:
        '''Run multi arm bandit'''
        recs = list()
        arm_keys = hashed_tasks.keys()
        sorted_qvalues = self._sort_and_augment_qvalues(qvalues, arm_keys)
        arm_history = set()
        while len(recs) < num_tasks:
            task = None
            if random.random() < self.epsilon:
                # random pull
                available_arms = list(arm_keys - arm_history)
                selected_arm = random.choice(available_arms)
            else:
                # select based on qvalue
                for arm, _ in sorted_qvalues:
                    if arm not in arm_history:
                        selected_arm = arm
                        break
            arm_history.add(selected_arm)
            arm_tasks = hashed_tasks[selected_arm]
            for t in arm_tasks:
                if t.get_id() not in self.last_tasks:
                    task = t
                    break
            if not task:
                task = arm_tasks[0]
                logger.warning(f'Using first task {task.get_name()} as no other tasks available')

            self.last_tasks[task.get_id()] = task.get_hash_code()
            recs.append(task)

        return recs

    def _update_qvalues(self, task_id: int = None) -> None:
        '''Set reward as 1 for selected task id, and 0 for others'''
        for t_id, t_hash in self.last_tasks.items():
            count = self.counts[self.last_context].get(t_hash, 0)
            count += 1
            reward = 1 if t_id == task_id else 0
            qv = self.qvalues[self.last_context][t_hash]
            qv += (reward - qv) * 1.0 / count
            self.qvalues[self.last_context][t_hash] = qv
            self.counts[self.last_context][t_hash] = count

    def recommend_tasks(self, tasks: List[TaskWrapper], num_tasks: int) -> List[TaskWrapper]:
        '''Contextual MAB recs'''
        # Flush old recs and update qvalues, counts
        if not self.task_chosen and self.last_context:
            self._update_qvalues()

        # load qvalues based on context
        qvalues = self._load_contextual_values()
        if qvalues:
            hashed_tasks = self._as_hashed_tasks(tasks)
            recs = self._run_mab(qvalues, hashed_tasks, num_tasks)
            return recs
        else:
            logger.warning('Returning random tasks')
            return tasks[:num_tasks]

    def update_chosen_task(self, task_id: int) -> None:
        self.task_chosen = True
        self._update_qvalues(task_id)
        return super().update_chosen_task(task_id)

    def load(self):
        '''Reload model'''
        self.qvalues, self.counts = self._load_model(self.mdl_file)

    def save(self):
        '''Save updated values'''
        with open(self.mdl_file, 'wb') as f:
            obj = {'qvalues': self.qvalues, 'counts': self.counts}
            pickle.dump(obj, f)
        return super().save()

class ContextEncoder:
    '''Encodes time of day into a numerical context'''
    def __init__(self, start_bound: int, end_bound: int, duration: int):
        '''Constructor'''
        self.start_bound = start_bound + duration
        self.end_bound = end_bound - duration
        self.duration = duration
        self.num_intervals = int((end_bound - start_bound) / duration)

    def get_context(self, hr: int) -> int:
        '''Get context based on hour'''
        if hr < self.start_bound:
            return 0
        elif hr >= self.end_bound:
            return int(self.num_intervals - 1)
        else:
            hr -= self.start_bound
            return int(hr / self.duration) + 1

    def get_num_intervals(self):
        '''Get total number of intervals'''
        return self.num_intervals
