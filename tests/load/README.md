# Record Linker – Locust Load Testing

This project includes a [Locust-based](https://locust.io/) load test suite for testing
performance of the Record Linker API.

## Setup

* Go through the development setup instructions in the [README](../README.md),
    this will install the necessary dependencies and set up a Python virtual environment.
```sh
source scripts/bootstrap.sh
```

* The load tests require 1 or 2 data files, to simulate the test.  At the very least, you'll need a data file
    with sample records in it, that the testing framework will use to send requests to the Record Linker API.
    This is called the `record-data` file.  You can use the [generate test data script](../scripts/gen_seed_test_data.py)
    to generate a sample file.  See that script for more details on how to create a test data file.
```sh
python scripts/gen_seed_test_data.py --count 100 > record-data.json
```

* [OPTIONAL] The `seed-data` file, can be used to seed the database with records before the test starts.
    This is optional, as its fine to start the test from an empty database.  Again, you can use the same
    [generate test data script](../scripts/gen_seed_test_data.py) to generate a test seed data file.
```sh
python scripts/gen_seed_test_data.py --count 9999 > seed-data.json
```

* [OPTIONAL] A scrambling script has been included to randomize the data in the test data files. See
    [scramble data script](scripts/scramble_data.py) for more details.

* The locust test suite will need an instance of the Record Linker API running.  This could be a local instance,
    or possibly over the network.  For a simple test, you can use the [local server script](../scripts/local_server.sh).
    See the [README](../README.md) for more details on a local setup and how to run the local server.
```sh
./scripts/local_server.sh
```

## Running the Locust Test Suite

To run the Locust test for 10 seconds with a load of 2 users and 100 records to link, use the following command:

```bash
locust -f locustfile.py \
    --headless \
    -u 2 -r 2 \
    --run-time 10s \
    --records-to-link 100 \
    --record-data assets/test_data.json
```

### Custom Parameters

| Argument             | Type     | Default                 | Description                                         |
|----------------------|----------|-------------------------|-----------------------------------------------------|
| `--records-to-link`  | `int`    | `0`                     | Number of records to link in the test run, 0 for infinite. |
| `--link-probability` | `float`  | `0.5`                   | Probability that any given record will be linked.  |
| `--seed-data`        | `str`    | ` `                     | Path to the seed data file.                        |
| `--record-data`      | `str`    | `assets/test_data.json` | Path to the record data file.                      |
| `--linkage-endpoint` | `choice` | `match`                 | Which linkage endpoint to test, `match` or `link`  |

### UI mode

You can run the tests, and control the parameters, in the browser by removing the `--headless` flag.
Visit http://localhost:8089 to view the UI.

```sh
locust -f locustfile.py
```

### 📍 Notes

See `locust --help` for information on more options.
