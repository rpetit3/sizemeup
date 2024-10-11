import gzip
import logging
import tarfile
from io import BytesIO
from itertools import batched
from pathlib import Path

import requests

NCBI_CATEGORY_IDS = {
    "2": "bacteria",
    "2157": "archaea",
    "2759": "eukaryota",
    "4751": "fungi",
    "10239": "virus",
    "12908": "unclassified",
    "28384": "other",
}

NCBI_GENOME_SIZE_URL = (
    "https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/species_genome_size.txt.gz"
)


def get_genome_sizes(outdir: str, ncbi_api_key: str, chunk_size:int, force: bool) -> dict:
    """
    Get the genome sizes from NCBI

    FROM NCBI (https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/README_species_genome_size.txt):

    The species_genome_size.txt.gz file has 6 tab-delimited columns. 
    Header rows begin with '#".

    Column  1: species_taxid
    Taxonomic identifier of each species 

    Column  2: min_ungapped_length
    Minimum expected ungapped genome size of an assembly for the species 

    Column  3: max_ungapped_length
    Maximum expected ungapped genome size of an assembly for the species 

    Column  4: expected_ungapped_length
    Median genome assembly size of assemblies for the species 

    Column  5: number_of_genomes
    Number of genomes used to calculate the expected size range

    Column 6: method_determined
        The method that was used to determine the size range. The three possible
        values are: 
            automatic: range set by the automatic process found in 
            https://www.ncbi.nlm.nih.gov/assembly/help/genome-size-check/
            manually-set: range set based on curated knowledge of the species 
            reference-genome: the range is determined by the reference genome
            for the species

    Args:
        outdir (str): The path to save the extracted targets
        ncbi_api_key (str): The API key to use for the NCBI API
        chunk_size (int): The size of the chunks to split the list into
        force (bool): Force the download of the genome sizes if it exists

    Returns:
        dict: A dictionary of genome sizes, where the taxid is the key

    """
    genome_sizes = {}
    genome_sizes_file = download_genome_sizes(outdir, force)
    col_names = [
        "species_taxid",
        "min_ungapped_length",
        "max_ungapped_length",
        "expected_ungapped_length",
        "number_of_genomes",
        "method_determined",
    ]

    with gzip.open(genome_sizes_file, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            vals = line.strip().split("\t")
            row = dict(zip(col_names, vals))
            genome_sizes[row["species_taxid"]] = row
            genome_sizes[row["species_taxid"]]["source"] = "ncbi"

    logging.info(f"Found {len(genome_sizes)} genome sizes from NCBI")
    logging.info("Converting TaxIDs to species names")
    tax_names = taxid2name(list(genome_sizes.keys()), ncbi_api_key, chunk_size)
    for taxid, vals in tax_names.items():
        genome_sizes[taxid]["name"] = vals["name"]
        genome_sizes[taxid]["category"] = vals["category"]

    return genome_sizes


def download_genome_sizes(outdir: str, force: bool) -> None:
    """
    Download the genome sizes from NCBI

    Args:
        outdir (str): The path to save the extracted targets
        force (bool): Force the download of the genome sizes if it exists
    """
    outfile = f"{outdir}/species_genome_size.txt.gz"
    if not Path(outfile).exists() or force:
        logging.info(f"Downloading genome sizes from NCBI to {outdir}")
        with open(f"{outdir}/species_genome_size.txt.gz", "wb") as f:
            f.write(requests.get(NCBI_GENOME_SIZE_URL).content)
    else:
        logging.info(f"Genome sizes already downloaded to {outdir}, skipping download")

    return Path(outfile)


def taxid2name(taxids: list, ncbi_api_key: str, chunk_size: int) -> dict:
    """
    Convert a list of NCBI TaxIDs to species names.

    For this query we will use NCBI Datasets v2 API
    Docs: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/rest-api/

    For this we will query the following endpoint:
    https://api.ncbi.nlm.nih.gov/datasets/v2alpha/taxonomy/name_report

    It expects the query to be delivered via POST with the following JSON payload:
    {
        "taxons": [
            "1280",
            "1281"
        ],
        "returned_content": "METADATA",
        "page_size": 1000,
        "include_tabular_header": "INCLUDE_TABULAR_HEADER_FIRST_PAGE_ONLY",
        "page_token": "string",
        "table_format": "SUMMARY",
        "children": false,
        "ranks": [
            "SPECIES"
        ]
    }

    The query will then include the following headers:
        accept: application/json
        api-key: ncbi-api-key
        content-type: application/json

    NCBI will only allow a maximum for 1000 taxids per query, so we will need to
    split the list into chunks of a user defined size.

    Args:
        taxids (list): A list of NCBI TaxIDs
        ncbi_api_key (str): The API key to use for the NCBI API
        chunk_size (int): The size of the chunks to split the list into

    Returns:
        dict: A dictionary of TaxIDs and species names
    """
    logging.info(f"Converting {len(taxids)} TaxIDs to species names")
    logging.debug(f"Using NCBI API key: {ncbi_api_key}")
    tax_names = {}
    url = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/taxonomy"
    headers = {
        "accept": "application/json",
        "api-key": ncbi_api_key,
        "content-type": "application/json",
    }
    taxid_chunks = list(batched(taxids, chunk_size))
    for i, chunk in enumerate(taxid_chunks):
        logging.debug(f"Processing chunk {i} of {len(taxid_chunks)}")
        payload = {
            "taxons": chunk,
            "returned_content": "METADATA",
            "page_size": 1000,
            "include_tabular_header": "INCLUDE_TABULAR_HEADER_FIRST_PAGE_ONLY",
            "page_token": "string",
            "table_format": "SUMMARY",
            "children": False,
            "ranks": ["SPECIES"],
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        for row in data['taxonomy_nodes']:
            tax_id = str(row["taxonomy"]["tax_id"])
            tax_names[tax_id] = {
                "name": row["taxonomy"]["organism_name"],
                "category": "unknown",
            }

            matches = []
            for id in NCBI_CATEGORY_IDS.keys():
                if int(id) in row["taxonomy"]["lineage"]:
                    matches.append(NCBI_CATEGORY_IDS[id])
            tax_names[tax_id]["category"] = ",".join(matches)

    logging.info(f"Converted {len(tax_names)} TaxIDs to species names")
    return tax_names


def species2taxid(species: list, ncbi_api_key: str, chunk_size: int) -> dict:
    """
    Convert a list of NCBI TaxIDs to species names.

    For this query we will use NCBI Datasets v2 API
    Docs: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/rest-api/

    For this we will query the following endpoint:
    https://api.ncbi.nlm.nih.gov/datasets/v2alpha/taxonomy/name_report

    It expects the query to be delivered via POST with the following JSON payload:
    {
        "taxons": [
            "1280",
            "1281"
        ],
        "returned_content": "METADATA",
        "page_size": 1000,
        "include_tabular_header": "INCLUDE_TABULAR_HEADER_FIRST_PAGE_ONLY",
        "page_token": "string",
        "table_format": "SUMMARY",
        "children": false,
        "ranks": [
            "SPECIES"
        ]
    }

    The query will then include the following headers:
        accept: application/json
        api-key: ncbi-api-key
        content-type: application/json

    NCBI will only allow a maximum for 1000 taxids per query, so we will need to
    split the list into chunks of a user defined size.

    Args:
        taxids (list): A list of NCBI TaxIDs
        ncbi_api_key (str): The API key to use for the NCBI API
        chunk_size (int): The size of the chunks to split the list into

    Returns:
        dict: A dictionary of TaxIDs and species names
    """
    logging.info(f"Converting {len(species)} species names to TaxIDs")
    logging.debug(f"Using NCBI API key: {ncbi_api_key}")
    tax_ids = {}
    url = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/taxonomy"
    headers = {
        "accept": "application/json",
        "api-key": ncbi_api_key,
        "content-type": "application/json",
    }
    species_chunks = list(batched(species, chunk_size))
    for i, chunk in enumerate(species_chunks):
        logging.debug(f"Processing chunk {i} of {len(species_chunks)}")
        payload = {
            "taxons": chunk,
            "returned_content": "METADATA",
            "page_size": 1000,
            "include_tabular_header": "INCLUDE_TABULAR_HEADER_FIRST_PAGE_ONLY",
            "page_token": "string",
            "table_format": "SUMMARY",
            "children": False,
            "ranks": ["SPECIES"],
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        for row in data['taxonomy_nodes']:
            if "taxonomy" in row:
                tax_id = str(row["taxonomy"]["tax_id"])
                name = row["taxonomy"]["organism_name"]
                tax_ids[name] = tax_id

    logging.info(f"Converted {len(tax_ids)} species names to TaxIDs")
    return tax_ids

