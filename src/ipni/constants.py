"""Basic constants."""

import os
from enum import StrEnum
from pathlib import Path

HOME = str(Path.home())
BIOKB_FOLDER = os.path.join(HOME, ".biokb")
PROJECT_NAME = "ipni"
PROJECT_FOLDER = os.path.join(BIOKB_FOLDER, PROJECT_NAME)
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
LOGS_FOLDER = os.path.join(DATA_FOLDER, "logs")  # where to store log files

DOWNLOAD_URL = "https://hosted-datasets.gbif.org/datasets/ipni.zip"
PATH_TO_ZIP_FILE = os.path.join(DATA_FOLDER, "ipni.zip")
DEFAULT_PATH_UNZIPPED_DATA_FOLDER = os.path.join(DATA_FOLDER, "unzipped")
DB_DEFAULT_CONNECTION_STR = "sqlite:///" + os.path.join(BIOKB_FOLDER, "biokb.db")


class TsvFileName(StrEnum):
    NAME = "Name.tsv"
    NAMES_RELATION = "NameRelation.tsv"
    TAXON = "Taxon.tsv"
    REFERENCE = "Reference.tsv"
    TYPE_MATERIAL = "TypeMaterial.tsv"
