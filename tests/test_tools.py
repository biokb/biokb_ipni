import pandas as pd

from ipni.tools import (
    clean_if_string,
    get_cleaned_and_standardized_dataframe,
    get_standard_column_name,
    get_standard_column_names,
)


def test_get_standard_column_name():
    test_str = "col:Aaa__Bbb  ccc #+* dddEee"
    expected_str = "aaa_bbb_ccc_ddd_eee"
    assert get_standard_column_name(test_str) == expected_str


def test_get_standard_column_names():
    columns = ["  col: aaa  %$!?BbbCcc", "  aaa    Bbb____ Ccc"]
    df = pd.DataFrame({}, columns=columns)
    expected = ["aaa_bbb_ccc", "aaa_bbb_ccc"]
    assert get_standard_column_names(df.columns) == expected


def test_clean_if_string():
    assert clean_if_string("  a       a     ") == "a a"
    assert clean_if_string(1) == 1


def test_get_cleaned_and_standardized_dataframe():
    test_df = pd.DataFrame(
        [("a         a ", 1), ("        a  a", 1)],
        columns=[" col: aaa  Bbb 56§%&/ccc", "&&Ddd  %&456eee Fff   "],
    )
    expected_df = pd.DataFrame(
        [
            ("a a", 1),
        ],
        columns=["aaa_bbb_ccc", "ddd_eee_fff"],
    )
    assert get_cleaned_and_standardized_dataframe(test_df).equals(expected_df)
