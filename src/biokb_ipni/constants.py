"""Basic constants."""

import os
from enum import StrEnum
from pathlib import Path

# standard for all biokb projects, but individual set
PROJECT_NAME = "ipni"
BASIC_NODE_LABEL = "DbIpni"
# standard for all biokb projects
ORGANIZATION = "biokb"
LIBRARY_NAME = f"{ORGANIZATION}_{PROJECT_NAME}"
HOME = str(Path.home())
BIOKB_FOLDER = os.path.join(HOME, f".{ORGANIZATION}")
PROJECT_FOLDER = os.path.join(BIOKB_FOLDER, PROJECT_NAME)
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
EXPORT_FOLDER = os.path.join(DATA_FOLDER, "ttls")
ZIPPED_TTLS_PATH = os.path.join(DATA_FOLDER, "ttls.zip")
SQLITE_PATH = os.path.join(BIOKB_FOLDER, f"{ORGANIZATION}.db")
DB_DEFAULT_CONNECTION_STR = "sqlite:///" + SQLITE_PATH
NEO4J_PASSWORD = "neo4j_password"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
LOGS_FOLDER = os.path.join(DATA_FOLDER, "logs")  # where to store log files
TABLE_PREFIX = PROJECT_NAME + "_"
os.makedirs(DATA_FOLDER, exist_ok=True)

# not standard for all biokb projects
DOWNLOAD_URL = "https://hosted-datasets.gbif.org/datasets/ipni.zip"
PATH_TO_ZIP_FILE = os.path.join(DATA_FOLDER, "ipni.zip")
DEFAULT_PATH_UNZIPPED_DATA_FOLDER = os.path.join(DATA_FOLDER, "unzipped")

class TsvFileName(StrEnum):
    NAME = "Name.tsv"
    NAMES_RELATION = "NameRelation.tsv"
    TAXON = "Taxon.tsv"
    REFERENCE = "Reference.tsv"
    TYPE_MATERIAL = "TypeMaterial.tsv"
