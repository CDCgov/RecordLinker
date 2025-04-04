# RecordLinker

[![codecov](https://codecov.io/github/CDCgov/RecordLinker/graph/badge.svg?token=V0FH691B9B)](https://codecov.io/github/CDCgov/RecordLinker)
[![release](https://img.shields.io/github/v/release/cdcgov/RecordLinker)](https://github.com/CDCgov/RecordLinker/releases)
[![python](https://img.shields.io/badge/python-3.11%2B-yellow)](https://docs.python.org/3.11/)

**General disclaimer** This repository was created for use by CDC programs to collaborate on public health related projects in support of the [CDC mission](https://www.cdc.gov/about/organization/mission.htm). GitHub is not hosted by the CDC, but is a third party website used by CDC and its partners to share information and collaborate on software. CDC use of GitHub does not imply an endorsement of any one particular service, product, or enterprise.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Testing](#testing)
- [Standard Notices](#standard-notices)

## Overview

The RecordLinker is a service that links records from two datasets based on a set of common attributes. The service is designed to be used in a variety of public health contexts, such as linking patient records from different sources or linking records from different public health surveillance systems. The service uses a probabilistic record linkage algorithm to determine the likelihood that two records refer to the same entity. The service is implemented as a RESTful API that can be accessed over HTTP. The API provides endpoints for uploading datasets, configuring the record linkage process, and retrieving the results of the record linkage process.

## Getting Started

### Pre-requisites

- Python 3.11 or higher
- [Docker](https://docs.docker.com/get-docker/)
- Node v20 or higher

### Initial Setup

Set up a Python virtual environment and install the required development dependencies:
NOTE: Sourcing the script is recommended over simply executing the script. This allows
the virtual environment to stay active in your shell.

```bash
source scripts/bootstrap.sh
```

Note: If you are running in WSL on a Windows machine, will need to run the bootstrap file directly with `./scripts/bootstrap.sh` and then activate the virtual environment by running `source .venv/bin/activate`.

### Running the API

To run the API locally, use the following command:

```bash
./scripts/local_server.sh --api-only
```

The API will be available at `http://localhost:8000/api`. Visit `http://localhost:8000/api/redoc` to view the API documentation.

### Running the application

To run the UI locally, use the following command:

```bash
./scripts/local_server.sh
```

The application will be available at `http://localhost:3000/`.

## Testing

The RecordLinker system comes with a number of built-in tests spread across several different types. Some of these tests are run automatically (e.g. by Github), while others must be manually executed by a developer.

- `tests/unit`: These comprise basic unit (and in some cases integration) tests providing code coverage to RecordLinker. These tests demonstrate the functionality of different parts of the code base under different logical conditions and with different inputs and outputs. They are automataically executed by a Github Actions workflow as part of a PR.
- `tests/algorithm`: This is a set of scripts developed to test an algorithm configuration with a known set of particular edge cases. In response to frequent questions of how the DIBBs algorithm handles case X, this mini-project was created to help answer those questions by giving developers some persistent evaluation tools. These tests are _not_ automated, and developers will need to go through the steps in the README in the relevant directory in order to run them.
- `tests/performance`: Another set of scripts developed to see how fast the API can process linkage requests using synthetic data. This is useful for verifying refactors are still performant and helping developers identify bottlenecks along the way. These tests are _not_ automated, and developers need to go through the steps in the README of the relevant directory in order to run them.

### Running unit tests

To run all the unit tests, use the following command:

```bash
pytest
```

To run a single unit test, use the following command:

```bash
pytest tests/unit/test_utils.py::test_bind_functions
```

### Running type checks

To run type checks, use the following command:

```bash
mypy
```

### Running code formatting checks

To run code formatting checks, use the following command:

```bash
ruff check
```

To run linting checks on the ui code, use the following command in the `ui` folder:

```bash
npm run lint
```

To run auto formatting on the ui code, use the following command in the `ui` folder:

```bash
npm run prettier:fix
```

For more information on developer workflows, see the [Developer Guide](docs/developer_guide.md).

## Standard Notices

### Public Domain Standard Notice

This repository constitutes a work of the United States Government and is not
subject to domestic copyright protection under 17 USC § 105. This repository is in
the public domain within the United States, and copyright and related rights in
the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
All contributions to this repository will be released under the CC0 dedication. By
submitting a pull request you are agreeing to comply with this waiver of
copyright interest.

### License Standard Notice

The repository utilizes code licensed under the terms of the Apache Software
License and therefore is licensed under ASL v2 or later.

This source code in this repository is free: you can redistribute it and/or modify it under
the terms of the Apache Software License version 2, or (at your option) any
later version.

This source code in this repository is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the Apache Software License for more details.

You should have received a copy of the Apache Software License along with this
program. If not, see http://www.apache.org/licenses/LICENSE-2.0.html

The source code forked from other open source projects will inherit its license.

### Privacy Standard Notice

This repository contains only non-sensitive, publicly available data and
information. All material and community participation is covered by the
[Disclaimer](DISCLAIMER.md)
and [Code of Conduct](CODE_OF_CONDUCT.md).
For more information about CDC's privacy policy, please visit [http://www.cdc.gov/other/privacy.html](https://www.cdc.gov/other/privacy.html).

### Contributing Standard Notice

Anyone is encouraged to contribute to the repository by [forking](https://help.github.com/articles/fork-a-repo)
and submitting a pull request. (If you are new to GitHub, you might start with a
[basic tutorial](https://help.github.com/articles/set-up-git).) By contributing
to this project, you grant a world-wide, royalty-free, perpetual, irrevocable,
non-exclusive, transferable license to all users under the terms of the
[Apache Software License v2](http://www.apache.org/licenses/LICENSE-2.0.html) or
later.

All comments, messages, pull requests, and other submissions received through
CDC including this GitHub page may be subject to applicable federal law, including but not limited to the Federal Records Act, and may be archived. Learn more at [http://www.cdc.gov/other/privacy.html](http://www.cdc.gov/other/privacy.html).

### Records Management Standard Notice

This repository is not a source of government records, but is a copy to increase
collaboration and collaborative potential. All government records will be
published through the [CDC web site](http://www.cdc.gov).

### Related documents

- [Open Practices](docs/policies/open_practices.md)
- [Rules of Behavior](docs/policies/rules_of_behavior.md)
- [Thanks and Acknowledgements](doc/policies/thanks.md)
- [Disclaimer](DISCLAIMER.md)
- [Contribution Notice](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

### Additional Standard Notices

Please refer to [CDC's Template Repository](https://github.com/CDCgov/template) for more information about [contributing to this repository](https://github.com/CDCgov/template/blob/main/CONTRIBUTING.md), [public domain notices and disclaimers](https://github.com/CDCgov/template/blob/main/DISCLAIMER.md), and [code of conduct](https://github.com/CDCgov/template/blob/main/code-of-conduct.md).
