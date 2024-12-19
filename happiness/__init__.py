from pathlib import Path

def _get_package_root():
    '''Gets the root directory of the current package.'''
    return Path(__file__).resolve().parent

def _get_model_dir():
    '''Gets the models directory'''
    return Path(__file__).resolve().parent.parent / 'models'

ROOT_DIR = _get_package_root()
MODEL_DIR = _get_model_dir()