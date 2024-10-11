import gzip
import logging

from bactopia.utils import download_url, file_exists, validate_file


def download_atb_file(atb_file: str, atb_url: str, progress: bool = False):
    """
    Download the ATB specific file if it doesn't exist

    Args:
        atb_file_ (str): The path to the ATB file list
        atb_url (str): The URL to download the ATB file list
        progress (bool): Display a progress bar
    """
    if file_exists(atb_file):
        logging.info(f"Using existing file list: {atb_file}")
        atb_file = validate_file(atb_file)
    else:
        logging.info(f"Downloading file list to: {atb_file}")
        atb_file = download_url(atb_url, atb_file, progress)
    return atb_file


def parse_assembly_stats(file_list: str) -> list:
    """
    Parse the ATB assembly_stats file list

    Args:
        file_list (str): The path to the ATB assembly_stats file list

    # Assembly Stats columns
        sample
        total_length
        number
        mean_length
        longest
        shortest
        N_count
        Gaps
        N50
        N50n
        N70
        N70n
        N90
        N90n

    We'll use the total_length for our rough estimate of the genome size

    Returns:
        list: A list of dictionaries containing the assembly_stats information
    """
    assembly_stats = {}
    cols = []
    with gzip.open(file_list, 'rt') as fh:
        for line in fh:
            data = line.rstrip().split("\t")
            if not cols:
                cols = data
            else:
                assembly_stats[data[0]] = dict(zip(cols, data))
    return assembly_stats
