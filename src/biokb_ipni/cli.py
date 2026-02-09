import logging
import os
from typing import Optional

import click
from sqlalchemy import create_engine

from biokb_ipni import __version__
from biokb_ipni.api.main import run_api
from biokb_ipni.constants import DB_DEFAULT_CONNECTION_STR, NEO4J_URI, NEO4J_USER
from biokb_ipni.db.manager import DbManager
from biokb_ipni.rdf.neo4j_importer import Neo4jImporter
from biokb_ipni.rdf.turtle import TurtleCreator

logger = logging.getLogger(__name__)


def setup_logging(ctx, param, value):
    # Only set up logging if the user actually asks for it
    if value == 1:
        logging.getLogger("biokb_ipni").setLevel(logging.INFO)
    elif value >= 2:
        logging.getLogger("biokb_ipni").setLevel(logging.DEBUG)

    # We must add a handler so the logs actually print to the screen
    if value > 0:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logging.getLogger("fetcher").addHandler(ch)

    return value


@click.group()
@click.version_option(__version__)
@click.option(
    "-v",
    count=True,
    callback=setup_logging,
    expose_value=False,
    help="Increase verbosity (use -vv for debug level)",
)
def main():
    """Import in RDBMS, create turtle files and import into Neo4J.

    Please follow the steps:\n
    1. Import data using `import-data` command.\n
    2. Create TTL files using `create-ttls` command.\n
    3. Import TTL files into Neo4j using `import-neo4j` command.\n
    """
    pass


@main.command("import-data")
@click.option(
    "-f",
    "--force-download",
    is_flag=True,
    type=bool,
    default=False,
    help="Force re-download of the source file [default: False]",
)
@click.option(
    "-d",
    "--delete-files",
    is_flag=True,
    type=bool,
    default=False,
    help="Delete downloaded source files after import [default: False]",
)
@click.option(
    "-c",
    "--connection-string",
    type=str,
    default=DB_DEFAULT_CONNECTION_STR,
    help=f"SQLAlchemy engine URL [default: {DB_DEFAULT_CONNECTION_STR}]",
)
def import_data(
    force_download: bool, connection_string: str, delete_files: bool
) -> None:
    """Import data.

    Args:
        force_download (bool): Force re-download of the source file (default: False)
        connection_string (str): SQLAlchemy engine URL (default: sqlite:///~/.biokb/biokb.db)
        delete_files (bool): Delete downloaded source files after import (default: False)
    """
    engine = create_engine(connection_string)
    DbManager(engine=engine).import_data(
        force_download=force_download, delete_files=delete_files
    )
    logger.info(f"Data imported successfully to {connection_string}")


@main.command("create-ttls")
@click.option(
    "-c",
    "--connection-string",
    type=str,
    default=DB_DEFAULT_CONNECTION_STR,
    help=f"SQLAlchemy engine URL [default: {DB_DEFAULT_CONNECTION_STR}]",
)
def create_ttls(connection_string: str):
    """Create TTL files from local database.

    Args:
        connection_string (str): SQLAlchemy engine URL (default: sqlite:///~/.biokb/biokb.db)
    """
    path_to_zip = TurtleCreator(create_engine(connection_string)).create_ttls()
    click.echo(
        f"Path to the zip file containing all generated Turtle files. {path_to_zip}"
    )


neo4j_uri = os.getenv("NEO4J_URI", NEO4J_URI)
neo4j_user = os.getenv("NEO4J_USER", NEO4J_USER)


@main.command("import-neo4j")
@click.option(
    "--uri",
    "-i",
    default=neo4j_uri,
    help=f'Neo4j URI [default="{neo4j_uri}"]',
)
@click.option(
    "--user",
    "-u",
    default=neo4j_user,
    help=f'Neo4j username [default="{neo4j_user}"]',
)
@click.option("--password", "-p", default=None, required=False, help="Neo4j password")
def import_neo4j(uri: str, user: str, password: Optional[str]):
    """Import TTL files into Neo4j database."""
    if password is None:
        password = click.prompt(
            "Please enter the Neo4j password (input will be hidden)", hide_input=True
        )
    else:
        click.echo(
            "It is not recommended to provide the Neo4j password via command line."
        )

    Neo4jImporter(neo4j_uri=uri, neo4j_user=user, neo4j_pwd=password).import_ttls()


@main.command("run-server")
@click.option(
    "--host", "-h", default="0.0.0.0", help="API server host [default: 0.0.0.0]"
)
@click.option("--port", "-P", default=8000, help="API server port [default: 8000]")
@click.option("--user", "-u", default="admin", help="API username [default=admin]")
@click.option("--password", "-p", default="admin", help="API password [default: admin]")
def run_server(host: str, port: int, user: str, password: str) -> None:
    """Run the API server.

    Args:
        host (str): API server host
        port (int): API server port
        user (str): API username
        password (str): API password
    """
    # set env variables for API authentication
    os.environ["API_USER"] = user
    os.environ["API_PASSWORD"] = password
    host_shown = "127.0.0.1" if host == "0.0.0.0" else host
    click.echo(f"API server running at http://{host_shown}:{port}/docs#/")
    run_api(host=host, port=port)


if __name__ == "__main__":
    main()
