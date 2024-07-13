import asyncio
from asyncio import timeout as async_timeout
from datetime import datetime

import click
from bleak import BleakScanner

from swb_meter.db import get_meter_table, get_temperature_table
from swb_meter.logger import logger
from swb_meter.parser import parse_advertisement_data


class DataHandler:
    """A class that handles data received from SwitchBot devices.

    Attributes:
        t (TemperatureTable): The temperature table used for data insertion.

    Methods:
        on_data(advertisement_data): Processes the advertisement data and inserts it into the temperature table.

    """

    def __init__(self):
        self.t = get_temperature_table()

    def on_data(self, advertisement_data):
        parsed_data = parse_advertisement_data(advertisement_data)

        if not parsed_data:
            return False

        insert_dict = {
            "mac_address": parsed_data.manufacturer_data.mac_address,
            "temperature": parsed_data.service_data.temperature.value,
            "scale": parsed_data.service_data.temperature.scale,
            "humidity": parsed_data.service_data.humidity,
            "battery": parsed_data.service_data.battery,
            "rssi": int(
                parsed_data.rssi
            ),  # `objc._pythonify.OC_PythonLong`型でエラーが出るのでintに変換
            "tx_power": parsed_data.tx_power,
            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # タイムスタンプを追加
        }

        self.t.insert(insert_dict)
        logger.info("inserted data.")
        logger.debug(parsed_data)

        return True


@click.group()
@click.version_option()
def cli():
    """SwitchBot Meters Server CLI tool.

    `swb-meter` allows you to listen for SwitchBot meters and insert the data into a SQLite database.

    By default the backend database is configured current directory with the name `swb_meter.db` (created if not exists).

    To change the database path by setting the environment variable `SWB_METER_DB_PATH`:

    \b
        $ export SWB_METER_DB_PATH=/path/to/db.sqlite

    \b
        or:

    \b
        $ SWB_METER_DB_PATH=/path/to/db.sqlite swb-meter listen


    To get started, add a meter with an alias (typically the room name where the meter is located) with its MAC address:

    \b
        $ swb-meter add "Living Room" 12:34:56:78:90:AB

    This will add a record to the `Meter` table.

    \b
        $ swb-meter ls
        Living Room 12:34:56:78:90:AB
        Total: 1 meters

    Then, start listening for the meters:

    \b
        $ swb-meter listen

    The data will be inserted into the `Temperature` table in the database.


    To visualize the data, you can run the Streamlit app in another terminal.
    You need optional dependencies [streamlit] installed:

    \b
        $ pip install swb-meter[streamlit]

    then run the Streamlit app:

    \b
        $ swb-meter streamlit


    By default, the log level is set to `INFO`.

    To change log level, set environment variable `SWB_METER_LOG_LEVEL=DEBUG` for verbose output.

    \b
        $ export SWB_METER_LOG_LEVEL=DEBUG

        or:

    \b
        $ SWB_METER_LOG_LEVEL=DEBUG swb-meter listen
    """


@cli.command(name="add")
@click.argument("alias", type=str, required=True)
@click.argument("mac_address", type=str, required=True)
@click.option("-u", "--upsert", is_flag=True, help="Upsert the existing record's alias")
def add_meter(alias, mac_address, upsert):
    """Add a SwitchBot meter to the master table with an alias.

    Example:
    \b

        $ swb-meter add "Living Room" 12:34:56:78:90:AB
    """

    # validate mac_address format
    if not mac_address.count(":") == 5:
        click.echo("Invalid MAC address format")
        return

    m = get_meter_table()

    if upsert:
        m.upsert({"alias": alias, "mac_address": mac_address}, pk="mac_address")
        click.echo("Upserted a meter")
    else:
        m.insert({"alias": alias, "mac_address": mac_address}, pk="mac_address")
        click.echo("Added a meter")


@cli.command(name="ls")
def list_meters():
    """List all SwitchBot meters in the master table.

    Example:
    \b

        $ swb-meter ls
    """
    m = get_meter_table()

    if not m.exists():
        click.echo("No meters added yet.")
        return

    for row in m.rows:
        click.echo(row)

    click.echo(f"Total: {m.count} meters")


@cli.command(name="rm")
@click.argument("mac_address", type=str, required=True)
def remove_meter(mac_address):
    """Remove a SwitchBot meter from the master table.

    Example:
    \b

        $ swb-meter rm 12:34:56:78:90:AB
    """

    m = get_meter_table()
    m.delete(mac_address)
    click.echo("Removed a meter")


@cli.command(name="listen")
@click.option(
    "-t",
    "--timeout",
    type=float,
    default=10,
    help="Timeout in seconds for each scan",
)
@click.option(
    "-i",
    "--interval",
    default=60,
    type=int,
    help="Interval in seconds between scans",
)
@click.option(
    "-s",
    "--scans",
    default=None,
    type=int,
    help="Number of scans. Default is None (infinite)",
)
def listen(timeout, interval, scans):
    """Listen for SwitchBot meters and insert data into the temperature table.

    This command listens for SwitchBot meters and inserts the data into the temperature table.
    For each scan, wait for the specified timeout duration until all data is found and inserted once for each meter.
    The interval option specifies the time to wait between scans.


    Example:
    \b

        $ swb-meter listen
    \b

        $ swb-meter listen -t 10 -i 60 # Timeout 10 seconds, Interval 60 seconds
    """

    handler = DataHandler()

    m = get_meter_table()
    mac_address = [row["mac_address"] for row in m.rows_where(select="mac_address")]

    async def _run(scans=scans):
        while scans != 0:  # 無限ループでスキャンを繰り返す
            # a copy from global mac_address
            look_for = mac_address.copy()

            try:
                async with BleakScanner(
                    cb=dict(use_bdaddr=True)
                ) as scanner, async_timeout(timeout):
                    logger.info(f"Start scanning for {timeout} seconds")
                    async for bd, ad in scanner.advertisement_data():
                        logger.debug(f"Looking for {look_for}")

                        if bd.address not in look_for:
                            logger.debug(f"not found device {bd.address}")
                            continue

                        logger.info(f"Found device {bd.address}")
                        res = handler.on_data(ad)
                        if res:
                            look_for.remove(bd.address)

                        if not look_for:
                            logger.info("All devices found")
                            break

            except asyncio.TimeoutError:
                logger.info("Timeout")

            if scans:
                scans -= 1
                logger.info(f"Scans left: {scans}")

            await asyncio.sleep(interval)

    asyncio.run(_run())


@cli.command(name="streamlit")
def run_app():
    """Run the Streamlit app for visualizing the temperature data.

    Example:
    \b
    $ swb-meter app
    """
    # check if streamlit is installed
    # or suggest to install it via optional dependencies [streamlit]
    try:
        from streamlit.web import cli as stcli
    except ImportError:
        click.echo(
            "Streamlit is not installed. Install it via optional dependencies [streamlit]"
        )
        return

    import sys
    from pathlib import Path

    sys.argv = ["streamlit", "run", str(Path(__file__).parent / "streamlit.py")]
    sys.exit(stcli.main())
