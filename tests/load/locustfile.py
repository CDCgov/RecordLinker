import json
import os
import pathlib
import random

import ijson
import locust
from locust import events


def str_to_bool(value):
    """
    Helper function to convert a string representation of truth to a boolean value in
    locust CLI.
    """
    if isinstance(value, bool):
        return value
    if value.lower() in {"true", "1", "yes"}:
        return True
    elif value.lower() in {"false", "0", "no"}:
        return False
    else:
        raise ValueError(f"Invalid boolean value: {value}")


@locust.events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--records-to-link", type=int, default=100, help="Number of records to link in the test run"
    )
    parser.add_argument(
        "--link-probability",
        type=float,
        default=0.5,
        help="Probability of linking a record",
    )

    parser.add_argument(
        "--seeded",
        type=str_to_bool,
        default=True,
        help="Indicates if the database has been seeded with initial data",
    )


class LoadTest(locust.HttpUser):
    host = "http://localhost:8080"
    auto_name_stripping = False

    def on_start(self):
        # Check if the database has been seeded before starting the test
        seeded = self.environment.parsed_options.seeded

        if not seeded:
            locust_file = pathlib.Path(__file__).resolve()
            project_root = locust_file.parents[2]
            seed_data_path = os.path.join(project_root, "tests/load/assets/seed_data.json")
            with open(seed_data_path, "rb") as input_file:
                clusters_iter = ijson.items(input_file, "clusters.item", use_float=True)
                chunk = []
                chunk_size = 100
                for cluster in clusters_iter:
                    chunk.append(cluster)
                    if len(chunk) == chunk_size:
                        seed_data = json.dumps({"clusters": chunk}, indent=2)
                        self.client.post("/api/seed", seed_data)
                        chunk = []

                if chunk:
                    seed_data = json.dumps({"clusters": chunk}, indent=2)
                    self.client.post("/api/seed", seed_data)

    @locust.task
    def link(self):
        """
        Loops through the original data, randomly selects records, and links them.
        """
        records_to_link = self.environment.parsed_options.records_to_link

        # Pick a random record from the seed data
        locust_file = pathlib.Path(__file__).resolve()
        project_root = locust_file.parents[2]
        original_data_path = os.path.join(project_root, "tests/load/assets/test_data.json")

        with open(original_data_path, "rb") as input_file:
            clusters_iter = ijson.items(input_file, "clusters.item", use_float=True)
            counter = 0
            for cluster in clusters_iter:
                for record in cluster["records"]:
                    # decide whether to link or not
                    if random.random() < self.environment.parsed_options.link_probability:
                        counter += 1
                        data = {
                            "record": record,
                            "external_person_id": cluster["external_person_id"],
                        }
                        with self.client.post("/api/match", json=data, catch_response=True) as resp:
                            try:
                                grade = resp.json().get("match_grade", "unknown")
                                # Override the request name based on match_grade
                                resp.request_meta["name"] = f"match_grade::{grade}"
                                resp.success()
                            except Exception as e:
                                resp.name = "match_grade::error"
                                resp.failure(str(e))

                        if counter >= records_to_link:
                            self.environment.runner.quit()
