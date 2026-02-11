import json

def load_song(path):
    with open(path, "r") as f:
        return json.load(f)
