#!/usr/bin/env python
"""
scripts/gen_seed_test_data.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Script to generate test data for the /seed endpoint in the RecordLinker project.

The script will emit a JSON object to STDOUT containing a list of clusters, each with a
list of PII records. By default, 100 clusters will be generated, each with a random number
of PII records up to 25. Those values can be adjusted see --help for more information.
"""

import argparse
import random

from faker import Faker

from recordlinker import schemas
from recordlinker.schemas.identifier import Identifier
from recordlinker.schemas.pii import Address
from recordlinker.schemas.pii import Gender
from recordlinker.schemas.pii import Name
from recordlinker.schemas.pii import Race
from recordlinker.schemas.pii import Sex
from recordlinker.schemas.pii import Telecom


def _generate_random_identifiers(count, faker):
    """
    Given a count of identifiers to generate, generate a list of
    MRNs, SSNs, and Drivers Licenses.
    """
    for idx in range(count):
        if idx % 3 == 0:
            # make mrn
            yield Identifier(type="MR", value=faker.bothify(text="MRN-#######"))
        if idx % 3 == 1:
            # make ssn
            yield Identifier(type="SS", value=faker.ssn())
        if idx % 3 == 2:
            # make drivers_license
            yield Identifier(
                type="DL", value=faker.bothify(text="DL-######"), authority=faker.state_abbr()
            )


# Function to generate random data
def _generate_random_pii_record(faker):
    return schemas.PIIRecord(
        external_id=faker.uuid4(),
        birth_date=faker.date_of_birth(minimum_age=0, maximum_age=100),
        sex=random.choice(list(Sex)),
        address=[
            Address(
                line=[faker.street_address()],
                city=faker.city(),
                state=faker.state_abbr(),
                postal_code=faker.zipcode(),
                county=faker.city(),
                country=faker.country_code(),
                latitude=faker.latitude(),
                longitude=faker.longitude(),
            )
        ],
        name=[
            Name(
                family=faker.last_name(),
                given=[faker.first_name()],
                use=random.choice(["official", "usual", "nickname"]),
            )
        ],
        telecom=[
            Telecom(
                value=faker.phone_number(),
                system="phone",
                use=random.choice(["home", "work", "mobile"]),
            )
        ],
        race=random.choice(list(Race)),
        gender=random.choice(list(Gender)),
        identifiers=list(_generate_random_identifiers(random.randint(1, 3), faker)),
    )


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Generate test data for the /seed endpoint")
    parser.add_argument("--count", type=int, default=100, help="The number of clusters to generate")
    parser.add_argument(
        "--max-per-cluster", type=int, default=25, help="The maximum number of records per cluster"
    )

    args = parser.parse_args()

    faker = Faker()
    clusters = []
    for _ in range(args.count):
        cluster = schemas.Cluster(
            external_person_id=f"EP:{str(faker.uuid4())}",
            records=[
                _generate_random_pii_record(faker)
                for _ in range(random.randint(1, args.max_per_cluster))
            ],
        )
        clusters.append(cluster)
    print(schemas.ClusterGroup(clusters=clusters).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
