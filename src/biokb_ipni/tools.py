import datetime
import re
from typing import Any, Iterable

import pandas as pd


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
