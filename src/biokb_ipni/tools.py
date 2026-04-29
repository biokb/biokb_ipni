import datetime
import logging
import os
import re
from typing import Any, Iterable, Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from biokb_ipni.constants import DB_DEFAULT_CONNECTION_STR

logger = logging.getLogger(__name__)


def get_engine(
    connection_string: Optional[str], env: Optional[str] = None
) -> Optional[Engine]:
    """Get a SQLAlchemy engine based on the provided connection string or environment file.
    The function prioritizes environment variables in the following order:
        1. -c/--connection-string option specifying the connection string directly
        2. -e/--env option specifying the environment file with CONNECTION_STR variable
        3. .env file with CONNECTION_STR variable
        4. Default connection string (sqlite:///~/.biokb/biokb.db)
    Args:
        connection_string (Optional[str]): SQLAlchemy engine URL (default: None)
        env (Optional[str]): Environment file to load for configuration (default: None)
    Returns:
        Optional[Engine]: SQLAlchemy engine if connection string is valid, otherwise None
    """
    engine: Engine | None = None
    if connection_string:
        try:
            engine = create_engine(connection_string)
            # check if the engine can connect to the database
            with engine.connect() as con:
                con.execute(text("SELECT 1"))
        except OperationalError as e:
            raise ValueError(
                "Failed to create engine with provided connection string. Please check the connection string and try again. "
                f"Original error: {e}"
            )
    elif env:
        # check if the provided env file exists
        if not os.path.exists(env):
            raise ValueError(
                f"Provided environment file {env} does not exist. Please provide a valid environment "
                "file or specify the connection string directly with the -c argument."
            )
        logger.info(f"Loading CONNECTION_STR variables from {env} file.")
        load_dotenv(env, override=True)
        connection_string = os.getenv("CONNECTION_STR")
        if connection_string is None:
            raise ValueError(
                f"CONNECTION_STR environment variable not found in {env} file. Please provide a valid environment "
                "file with CONNECTION_STR or specify the connection string directly with the -c argument."
            )
        engine = create_engine(connection_string)
        try:
            with engine.connect() as con:
                con.execute(text("SELECT 1"))
        except OperationalError as e:
            raise ValueError(
                f"Failed to create engine with connection string \n'{connection_string}'\n from environment file {env}. Please check the connection string in the environment file and try again."
                f"Original error: {e}"
            )
    elif os.path.exists(".env"):
        logger.info("Loading CONNECTION_STR variables from .env file.")
        load_dotenv(".env", override=True)
        connection_string = os.getenv("CONNECTION_STR")
        if connection_string is None:
            raise ValueError(
                "CONNECTION_STR environment variable not found in .env file. "
                "Please provide a valid .env file or specify the connection string directly with the -c argument."
            )
        engine = create_engine(connection_string)
        try:
            with engine.connect() as con:
                con.execute(text("SELECT 1"))
        except OperationalError as e:
            raise ValueError(
                f"Failed to create engine with connection string \n'{connection_string}'\n from .env file. Please check the connection string in the .env file and try again."
                f"Original error: {e}"
            )
    if connection_string is None:
        logger.info(
            f"No environment file provided or CONNECTION_STR not found. Using default connection string {DB_DEFAULT_CONNECTION_STR}."
        )

    return engine


def get_standard_column_name(column_name: str) -> str:
    """Standardize a column name.

    Because all columns in IPNI have a lading "col:" in the column name, this is deleted.
    Remaining name is divided by upper cases and divided by underscore.

    Args:
        column_name (str): column name

    Returns:
        str: standardized column name
    """
    without_prefix = column_name.split(":")[-1].strip().replace("ID", "Id")
    results = re.findall(r"[A-Za-z][a-z]*", without_prefix)
    return "_".join(results).lower()


def get_standard_column_names(columns: Iterable[str]) -> list[str]:
    """Standardize a column names.

    Args:
        columns (Iterable[str]): column name

    Returns:
        list[str]: standardized column names
    """
    return [get_standard_column_name(col) for col in columns]


def clean_if_string(input: str | Any) -> str | Any:
    """Returns a string (if input is a string) which is stripped by white spaces and all multiple spaces are removed.

    Args:
        input (str | Any): string to clean of Any

    Returns:
        str | Any: string to clean of Any
    """
    if isinstance(input, str):
        return re.sub(r"\s{2,}", " ", input).strip()
    return input


def get_cleaned_and_standardized_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe in which all cells with strings
    1. multiple whitespaces are replaced by single whitespaces
    2. all whitespaces are stripped
    3. column names are standardized (check get_standard_column_name)
    4. Duplicates are removed

    Args:
        df (pd.DataFrame): pandas DataFrame

    Returns:
        pd.DataFrame: cleaned and standardized DataFrame
    """
    df.columns = get_standard_column_names(df.columns)
    df_new = df.map(lambda x: clean_if_string(x))
    df_new.drop_duplicates(inplace=True)
    return df_new


def parse_date(date):
    if pd.isna(date):  # Handle NaN values
        return pd.NaT
    else:
        found = re.search(
            r"^(?P<year>\d{2,4})-(?P<month>\d{1,2})(-(?P<day>\d{1,2}))?", date
        )
        if found:
            year = int(found["year"])
            month = int(found["month"])
            day = int(found["day"]) if found["day"] else 1
            day = 28 if (month == 2 and day > 28) else day
            return datetime.date(year, month, day)
        else:
            return pd.NaT  # If format is unknown
