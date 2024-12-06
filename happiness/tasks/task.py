'''Task wrapper over db model'''
from happiness.tasks.model import Task


class TaskWrapper:
    '''Task wrapper over db model'''
    def __init__(self, data: Task):
        '''Initialize task wrapper'''
        self._task_model = data
        self._rec_id = None
        self.hash_field_lookup = {
            'complexity': {'simple': 0, 'medium': 1, 'hard': 2},
            'type': {'chores': 0, 'learning': 1, 'constructive': 2, 'creative': 3},
            'priority': {'low': 0, 'medium': 1, 'high': 2},
            'repeatable': {1: 0, 0: 1}
        }

    def _get_attr(self, attr: str):
        '''Helper method to get attribute from task model'''
        return getattr(self._task_model, attr)

    def get_id(self) -> int:
        '''Get task id'''
        return self._get_attr('id')

    def get_name(self) -> str:
        '''Get task name'''
        return self._get_attr('name')

    def get_complexity(self) -> str:
        '''Get task complexity'''
        return self._get_attr('complexity')

    def get_type(self) -> str:
        '''Get task type'''
        return self._get_attr('type')

    def get_due_date(self) -> str:
        '''Get task due date'''
        return self._get_attr('due_date')

    def get_priority(self) -> str:
        '''Get task priority'''
        return self._get_attr('priority')

    def is_repeatable(self) -> bool:
        '''Check if task is repeatable'''
        return self._get_attr('repeatable')

    def get_status(self) -> str:
        '''Get task status'''
        return self._get_attr('status')

    def get_rec_id(self) -> int:
        '''Get recommendation ID'''
        return self._rec_id

    def set_rec_id(self, rec_id: int) -> None:
        '''Set recommendation ID'''
        self._rec_id = rec_id

    @staticmethod
    def from_dict(data: dict):
        '''Create task wrapper from dictionary'''
        return TaskWrapper(Task(**data))

    def get_hash_code(self):
        '''Return a hash value computed over fields'''
        value = 0
        for field, lookups in self.hash_field_lookup.items():
            fval = self._get_attr(field)
            val = lookups.get(fval, len(lookups))
            value = value << 3
            value += val
            if val not in lookups:
                lookups[fval] = val
        return value
