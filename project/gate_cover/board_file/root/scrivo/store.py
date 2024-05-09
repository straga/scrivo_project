import json
import asyncio
import time
import os

class JsonStore:
    _instances = {}
    _task = None
    _dir = 'store'

    def __init__(self, filename, delay=0):
        self.filename = filename
        self.delay = delay
        self.last_save_time = 0
        self.data = {}
        self.dir_path = self._dir
        try:
            os.stat(self.dir_path)
        except OSError as e:
            if e.args[0] == 2: # Directory not found
                os.mkdir(self.dir_path)
        file_path = "/".join([self.dir_path, self.filename])
        try:
            with open(file_path, 'r') as f:
                self.data = json.load(f)
        except OSError:
            with open(file_path, 'w') as f:
                json.dump(self.data, f)
        if file_path not in self._instances:
            self._instances[file_path] = self

    @classmethod
    async def _save_task(cls):
        while True:
            for instance in cls._instances.values():
                current_time = time.time()
                if current_time - instance.last_save_time > instance.delay:
                    file_path = "/".join([instance.dir_path, instance.filename])
                    with open(file_path, 'w') as f:
                        json.dump(instance.data, f)
                    instance.last_save_time = current_time
            await asyncio.sleep(1)

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    @classmethod
    def get_instance(cls, filename, delay=0):
        if cls._task is None:
            cls._task = asyncio.create_task(cls._save_task())
        file_path = "/".join([cls._dir, filename])
        if file_path not in cls._instances:
            cls._instances[file_path] = cls(filename, delay)
        return cls._instances[file_path]


# # Example usage
# from scrivo.store.store import JsonStore
# store1 = JsonStore.get_instance('mydata1.json', delay=60)
# store2 = JsonStore.get_instance('mydata2.json', delay=120)
# store1.set('name', 'John')
# store1.set('age', 30)
# store2.set('name', 'Jane')
# store2.set('age', 25)
