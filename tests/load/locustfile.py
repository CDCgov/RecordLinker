import json
import os
import pathlib
import random
import threading

import locust


class LoadTest(locust.HttpUser):
    seed_data = None
    seeded = False
    seed_lock = threading.Lock()

    def load_seed_data(self):
        locust_file = pathlib.Path(__file__).resolve()
        project_root = locust_file.parents[2]  # -> goes up to the project root
        json_path = os.path.join(project_root, "tests/load/assets/test_data.json")

        with open(json_path, "r") as f:
            return json.load(f)

    def on_start(self):
        with self.seed_lock:
            if not self.__class__.seeded:
                self.__class__.seed_data = self.load_seed_data()
                # TODO: Adjust to loop through the seed data; API endpoint has a limit of 100 clusters
                self.client.post("/api/seed", json=self.__class__.seed_data)
                self.__class__.seeded = True

    def pick_random_record(self):
        # Pick a random record from the seed data
        rando = random.choice(self.__class__.seed_data["clusters"])
        return rando

    @locust.task
    def link(self):
        random_data = self.pick_random_record()
        data = {
            "record": random_data["records"][0],
            "external_person_id": random_data["external_person_id"],
        }
        self.client.post("/api/link", json=data)

        print(f"Linking...{random_data['external_person_id']}")
