from rdflib.namespace import Namespace

BASE_URI = "https://ipni.org/"


BIOKB_BASE = Namespace("https://biokb.scai.fraunhofer.de/ipni/")

REL_NS = Namespace(BIOKB_BASE + "relation#")
NODE_NS = Namespace(BIOKB_BASE + "node#")
NCBI_TAXON_NS = Namespace("http://purl.obolibrary.org/obo/NCBITaxon_")
NAME_NS = Namespace(f"{BASE_URI}n/")
FAMILY_NS = Namespace(f"{BIOKB_BASE}family/")
LOCATION_NS = Namespace(f"{BIOKB_BASE}location/")
