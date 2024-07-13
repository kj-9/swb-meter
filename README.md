# swb-meter

[![PyPI](https://img.shields.io/pypi/v/swb-meter.svg)](https://pypi.org/project/swb-meter/)
[![Changelog](https://img.shields.io/github/v/release/kj-9/swb-meter?include_prereleases&label=changelog)](https://github.com/kj-9/swb-meter/releases)
[![Tests](https://github.com/kj-9/swb-meter/actions/workflows/test.yml/badge.svg)](https://github.com/kj-9/swb-meter/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/kj-9/swb-meter/blob/master/LICENSE)

switch-bot meters server



## Installation

Install this tool using `pip`:
```bash
pip install
```

## Usage

For help, run `swb-meter --help`:
<!-- [[[cog
import cog
from swb_meter import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["--help"])
help = result.output.replace("Usage: cli", "Usage: swb-meter")
cog.out(
    f"```bash\n{help}\n```"
)
]]] -->
```bash
Usage: swb-meter [OPTIONS] COMMAND [ARGS]...

  SwitchBot Meters Server CLI tool.

  `swb-meter` allows you to listen for SwitchBot meters and insert the data into
  a SQLite database.

  By default the backend database is configured current directory with the name
  `swb_meter.db` (created if not exists).

  To change the database path by setting the environment variable
  `SWB_METER_DB_PATH`:

      $ export SWB_METER_DB_PATH=/path/to/db.sqlite

      or:

      $ SWB_METER_DB_PATH=/path/to/db.sqlite swb-meter listen

  To get started, add a meter with an alias (typically the room name where the
  meter is located) with its MAC address:

      $ swb-meter add "Living Room" 12:34:56:78:90:AB

  This will add a record to the `Meter` table.

      $ swb-meter ls
      Living Room 12:34:56:78:90:AB
      Total: 1 meters

  Then, start listening for the meters:

      $ swb-meter listen

  The data will be inserted into the `Temperature` table in the database.

  To visualize the data, you can run the Streamlit app in another terminal. You
  need optional dependencies [streamlit] installed:

      $ pip install swb-meter[streamlit]

  then run the Streamlit app:

      $ swb-meter streamlit

  By default, the log level is set to `INFO`.

  To change log level, set environment variable `SWB_METER_LOG_LEVEL=DEBUG` for
  verbose output.

      $ export SWB_METER_LOG_LEVEL=DEBUG

      or:

      $ SWB_METER_LOG_LEVEL=DEBUG swb-meter listen

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  add        Add a SwitchBot meter to the master table with an alias.
  listen     Listen for SwitchBot meters and insert data into the...
  ls         List all SwitchBot meters in the master table.
  rm         Remove a SwitchBot meter from the master table.
  streamlit  Run the Streamlit app for visualizing the temperature data.

```
<!-- [[[end]]] -->

You can also use:
```bash
python -m swb_meter --help
```

### Commands

#### `swb-meter add`
<!-- [[[cog
import cog
from swb_meter import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["add", "--help"])
help = result.output.replace("Usage: cli", "Usage: swb-meter")
cog.out(
    f"```bash\n{help}\n```"
)
]]] -->
```bash
Usage: swb-meter add [OPTIONS] ALIAS MAC_ADDRESS

  Add a SwitchBot meter to the master table with an alias.

  Example: 

      $ swb-meter add "Living Room" 12:34:56:78:90:AB

Options:
  -u, --upsert  Upsert the existing record's alias
  --help        Show this message and exit.

```
<!-- [[[end]]] -->


#### `swb-meter ls`
<!-- [[[cog
import cog
from swb_meter import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["ls", "--help"])
help = result.output.replace("Usage: cli", "Usage: swb-meter")
cog.out(
    f"```bash\n{help}\n```"
)
]]] -->
```bash
Usage: swb-meter ls [OPTIONS]

  List all SwitchBot meters in the master table.

  Example: 

      $ swb-meter ls

Options:
  --help  Show this message and exit.

```
<!-- [[[end]]] -->


#### `swb-meter rm`
<!-- [[[cog
import cog
from swb_meter import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["rm", "--help"])
help = result.output.replace("Usage: cli", "Usage: swb-meter")
cog.out(
    f"```bash\n{help}\n```"
)
]]] -->
```bash
Usage: swb-meter rm [OPTIONS] MAC_ADDRESS

  Remove a SwitchBot meter from the master table.

  Example: 

      $ swb-meter rm 12:34:56:78:90:AB

Options:
  --help  Show this message and exit.

```
<!-- [[[end]]] -->


#### `swb-meter listen`
<!-- [[[cog
import cog
from swb_meter import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["listen", "--help"])
help = result.output.replace("Usage: cli", "Usage: swb-meter")
cog.out(
    f"```bash\n{help}\n```"
)
]]] -->
```bash
Usage: swb-meter listen [OPTIONS]

  Listen for SwitchBot meters and insert data into the temperature table.

  This command listens for SwitchBot meters and inserts the data into the
  temperature table. For each scan, wait for the specified timeout duration
  until all data is found and inserted once for each meter. The interval option
  specifies the time to wait between scans.

  Example: 

      $ swb-meter listen 

      $ swb-meter listen -t 10 -i 60 # Timeout 10 seconds, Interval 60 seconds

Options:
  -t, --timeout FLOAT     Timeout in seconds for each scan
  -i, --interval INTEGER  Interval in seconds between scans
  -s, --scans INTEGER     Number of scans. Default is None (infinite)
  --help                  Show this message and exit.

```
<!-- [[[end]]] -->


#### `swb-meter streamlit`
<!-- [[[cog
import cog
from swb_meter import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli.cli, ["streamlit", "--help"])
help = result.output.replace("Usage: cli", "Usage: swb-meter")
cog.out(
    f"```bash\n{help}\n```"
)
]]] -->
```bash
Usage: swb-meter streamlit [OPTIONS]

  Run the Streamlit app for visualizing the temperature data.

  Example:  $ swb-meter app

Options:
  --help  Show this message and exit.

```
<!-- [[[end]]] -->


## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd swb-meter
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```
