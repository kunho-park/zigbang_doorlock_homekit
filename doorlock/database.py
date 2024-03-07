import json, os


class Database:
    def __init__(self, path: str):
        self.path = path
        self.data = {}

    def load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, "r") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key: str, s=None):
        return self.data.get(key, s)

    def set(self, key: str, value):
        self.data[key] = value
        self.save()
