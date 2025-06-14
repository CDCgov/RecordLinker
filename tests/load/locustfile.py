import argparse
import json
import os
import pathlib
import random

import ijson
import locust


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


def normalized_value(val):
    """
    Helper function to convert a string representation of a float to a normalized value in
    locust CLI.
    """
    try:
        val = float(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{val} is not a valid float")
    if val <= 0.0 or val > 1.0:
        raise argparse.ArgumentTypeError(f"{val} not in range (0.0, 1.0]")
    return val


@locust.events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--records-to-link",
        type=int,
        default=0,
        help="Number of records to link in the test run, infinite if 0",
    )
    parser.add_argument(
        "--link-probability",
        type=normalized_value,
        default=0.5,
        help="Probability of linking a record",
    )
    parser.add_argument(
        "--seed-data",
        type=str,
        help="Path to the record data file to use when seeding the database",
    )
    parser.add_argument(
        "--record-data",
        type=str,
        default=f"{pathlib.Path(__file__).resolve().parent}/assets/test_data.json",
        help="Path to the record data file to use in the test run",
    )
    parser.add_argument(
        "--linkage-endpoint",
        choices=["match", "link"],
        default="match",
        help="The linkage endpoint to use in the test run",
    )


class LoadTest(locust.HttpUser):
    host = "http://localhost:8080/api"
    auto_name_stripping = False

    def on_start(self):
        options = self.environment.parsed_options
        if options.seed_data:
            if os.path.exists(options.seed_data):
                raise ValueError(f"Seed data file does not exist: {options.seed_data}")

            chunk_size = 100
            with open(options.seed_data, "r") as input_file:
                clusters_iter = ijson.items(input_file, "clusters.item", use_float=True)
                chunk = []
                for cluster in clusters_iter:
                    chunk.append(cluster)
                    if len(chunk) == chunk_size:
                        self.client.post("/seed", json.dumps({"clusters": chunk}))
                        chunk = []

                if chunk:
                    self.client.post("/seed", json.dumps({"clusters": chunk}))

    @locust.task
    def link(self):
        """
        Loops through the original data, randomly selects records, and links them.
        """
        options = self.environment.parsed_options
        # check if string is a valid path
        if not os.path.exists(options.record_data):
            raise ValueError(f"Record data file does not exist: {options.record_data}")

        with open(options.record_data, "r") as input_file:
            url = f"/{options.linkage_endpoint}"
            counter = 0
            for cluster in ijson.items(input_file, "clusters.item", use_float=True):
                data = {"external_person_id": cluster.get("external_person_id", None)}
                for record in cluster["records"]:
                    # decide whether to link or not
                    if random.random() < options.link_probability:
                        counter += 1
                        data["record"] = record
                        with self.client.post(url, json=data, catch_response=True) as resp:
                            try:
                                grade = resp.json().get("match_grade", "unknown")
                                # Override the request name based on match_grade
                                resp.request_meta["name"] = f"match_grade::{grade}"
                                resp.success()
                            except Exception as e:
                                resp.request_meta["name"] = "match_grade::error"
                                resp.failure(str(e))

                        if options.records_to_link and counter >= options.records_to_link:
                            self.environment.runner.quit()
