import json

class Config:
    def __init__(self, config_file):
        self._load_config(config_file)
    
    def _load_config(self, config_file):
        with open(config_file) as f:
            self._config = json.load(f)
    
    @property
    def models(self):
        return self._config.get('models', {})
    
    @property
    def classes(self):
        return self._config.get('classes', {})
    
    @property
    def tasks(self):
        return self._config.get('tasks', [])
    
    @property
    def detection_threshold(self):
        return self._config.get('detection_threshold', 0.5)
    
    def get_model_config(self, task_name):
        return self.models.get(task_name, {})
    
    def get_class_names(self, task_name):
        return self.classes.get(task_name, {})
    
    def get_preprocessing_params(self, task_name):
        return self._config.get('preprocessing', {}).get(task_name, {})
