import json
import pathlib
import random
import threading

import locust


class LoadTest(locust.HttpUser):
    seed_data = None
    seeded = False
    seed_lock = threading.Lock()

    def load_seed_data(self):
        """
        Loads the seed data from the JSON file.
        """
        locust_file = pathlib.Path(__file__).resolve()
        project_root = locust_file.parents[2]
        json_path = project_root / "src" / "recordlinker" / "assets" / "test_data.json"

        with open(json_path, "r") as f:
            return json.load(f)

    def on_start(self):
        """
        Called when a Locust user starts.
        TODO: Ensure this is only called once per test run; not once per user.
        """
        with self.seed_lock:
            if not self.__class__.seeded:
                self.__class__.seed_data = self.load_seed_data()
                self.client.post("/api/seed", json=self.__class__.seed_data)
                self.__class__.seeded = True

    def randomize_data(self):
        """
        Randomize a random record from the seed data.
        """
        rando = random.choice(self.__class__.seed_data["clusters"])
        # TODO: add refactored `apply_field_scrambling` function here once it's implemented
        return rando

    @locust.task
    def link(self):
        """
        Link a randomized record from the seed data.
        """
        random_data = self.randomize_data()
        data = {
            "record": random_data["records"][0],
            "external_person_id": random_data["external_person_id"],
        }
        self.client.post("/api/link", json=data)
