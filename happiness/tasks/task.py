'''Task wrapper over db model'''
from happiness.tasks.model import Task


class TaskWrapper:
    '''Task wrapper over db model'''
    def __init__(self, data: Task):
        '''Initialize task wrapper'''
        self._task_model = data

    def get_name(self) -> str:
        '''Get task name'''
        return self._task_model.name

    def get_complexity(self) -> str:
        '''Get task complexity'''
        return self._task_model.complexity

    def get_type(self) -> str:
        '''Get task type'''
        return self._task_model.type

    def get_due_date(self) -> str:
        '''Get task due date'''
        return self._task_model.due_date

    def get_priority(self) -> str:
        '''Get task priority'''
        return self._task_model.priority

    def is_repeatable(self) -> bool:
        '''Check if task is repeatable'''
        return self._task_model.repeatable

    def get_status(self) -> str:
        '''Get task status'''
        return self._task_model.status
    
    @staticmethod
    def from_dict(data: dict):
        '''Create task wrapper from dictionary'''
        return TaskWrapper(Task(**data))
