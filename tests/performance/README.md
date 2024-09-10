# Record Linkage Performance Testing

This repository hosts a performance testing project that focuses on assessing the
scalability and responsiveness of the
[record-linkage](https://github.com/CDCgov/phdi/tree/main/containers/record-linkage)
API. It employs [OpenTelemetry](https://opentelemetry.io) for instrumentation,
specifically to measure API latency and identify potential service bottlenecks.
This project does not attempt to evaluate the effectiveness of the underlying 
linkage algorithm.

## Prerequisites

Before getting started, ensure you have the following installed:

- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Setup

1. Build the Docker images:

    ```bash
    docker compose --profile perf build
    ```

2. Configure environment variables

    ```bash
    edit tests/performance/rlpt.env
    ```
    Edit the environment variables in the file to tune the test parameters

## Running Performance Tests

1. Run the Synthea tests

    ```bash
    docker compose --profile perf run --rm perf-runner scripts/test_synthea_data.sh
    ```

    This will generate a population of synthetic patients using Synthea. Extract
    the patient resources from the output and send them to the record-linkage API.

2. Analyze the results

    Both Jaeger and the MPI database will be available for analysis after the tests
    have completed. The Jaeger UI can be accessed at
    [http://localhost:16686](http://localhost:16686). While the MPI database can be
    accessed on port 5432, using the Postgres client of your choice. Additionally, a
    pgbadger report will be generated in the `tmp/results/psql` directory.


## Environment Variables

For the compose services, environment variables have been split across two attributes.

1. `env_file`: The attributes that should be tuned for your particular performance test,
    are located in the `rlpt.env` file.
2. `environment`: The attributes that should likely remain static for all performance
    tests, are located directly in the `compose.yml` file.

### Performance Test Parameters

The following environment variables can be tuned in the `rlpt.env` file:

- `POPULATION_SIZE`: The number of synthetic patients to generate using Synthea.
- `ITERATIONS`: The number of times to run the performance test on the same population,
    to see how the algorithm performs with multiple patients in a person cluster.
- `STATE`: The state to use when generating synthetic patients.
- `CITY`: The city to use when generating synthetic patients.
- `REDUCE_COMPARES`: Whether to reduce the number of comparisons in the linkage algorithm
    by combining patients records with the same attributes.

## Monitoring with OpenTelemetry

The API is instrumented with OpenTelemetry for monitoring and tracing purposes. You can
explore the collected metrics and traces using your preferred observability platform
compatible with OpenTelemetry, such as Jaeger or Prometheus.

By default, the OpenTelemetry collector is configured to export telemetry data to the
local instance of Jaeger, which can be accessed at
[http://localhost:16686](http://localhost:16686).

## Cleanup

After you've finished running performance tests and analyzing the results, you can stop and remove the Docker containers by running:

```bash
docker compose --profile perf down
```
