"""The data dictionary is generated from the dbt YAML and committed; keep the two in sync."""

from data import dictionary


def test_dictionary_is_up_to_date():
    dictionary.main(["--check"])  # if this fails, run `make data-docs` and commit the result
