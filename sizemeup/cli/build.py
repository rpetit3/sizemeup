import datetime
import logging
import os
import sys
from pathlib import Path
from statistics import mean

import rich
import rich.console
import rich.traceback
import rich_click as click
from rich import print
from rich.logging import RichHandler
from rich.table import Table

import sizemeup
from sizemeup.atb import download_atb_file, parse_assembly_stats
from sizemeup.ncbi import get_genome_sizes, species2taxid

from bactopia.atb import parse_atb_file_list
from bactopia.utils import download_url, file_exists, validate_file


# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "sizemeup-build": [
        {
            "name": "Required Options",
            "options": [
                "--outdir",
            ],
        },
        {
            "name": "NCBI API Options",
            "options": [
                "--ncbi-api-key",
                "--chunk-size",
            ],
        },
        {
            "name": "ATB Options",
            "options": [
                "--atb-file-list-url",
                "--atb-assembly-stats",
                "--min-genomes",
            ],
        },
        {
            "name": "Additional Options",
            "options": [
                "--user-sizes",
                "--force",
                "--verbose",
                "--silent",
                "--version",
                "--help",
            ],
        },
    ]
}


@click.command()
@click.version_option(sizemeup.__version__, "--version", "-V")
@click.option(
    "--outdir",
    "-o",
    required=True,
    help="The path to save the extracted targets",
)
@click.option(
    "--ncbi-api-key",
    "-k",
    required=False,
    default=os.environ.get("NCBI_API_KEY", None),
    help="The API key to use for the NCBI API",
)
@click.option(
    "--chunk-size",
    "-c",
    default=500,
    help="The size of the chunks to split the list into",
)
@click.option(
    "--atb-file-list-url",
    "-a",
    default="https://osf.io/download/4yv85/",
    show_default=True,
    help="The URL to the ATB file list",
)
@click.option(
    "--atb-assembly-stats-url",
    "-s",
    default="https://osf.io/download/nbyqv/",
    show_default=True,
    help="The name of the ATB assembly stats file",
)
@click.option(
    "--min-genomes",
    "-m",
    default=5,
    help="The minimum number of genomes to use for ATB species",
)
@click.option(
    "--user-sizes",
    "-u",
    required=False,
    help="A user-provided genome sizes file",
)
@click.option("--force", is_flag=True, help="Overwrite existing reports")
@click.option("--verbose", is_flag=True, help="Increase the verbosity of output")
@click.option("--silent", is_flag=True, help="Only critical errors will be printed")
def sizemeup_build(
    outdir: str,
    ncbi_api_key: str,
    chunk_size: int,
    atb_file_list_url: str,
    atb_assembly_stats_url: str,
    min_genomes: int,
    user_sizes: str,
    force: bool,
    verbose: bool,
    silent: bool,
):
    """sizemeup-build - Build the taxid and species genome sizes from NCBI"""
    # Setup logs
    logging.basicConfig(
        format="%(asctime)s:%(name)s:%(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            RichHandler(rich_tracebacks=True, console=rich.console.Console(stderr=True))
        ],
    )
    logging.getLogger().setLevel(
        logging.ERROR if silent else logging.DEBUG if verbose else logging.INFO
    )

    # Create the output directory
    logging.debug(f"Creating output directory: {outdir}")
    Path(outdir).mkdir(parents=True, exist_ok=True)

    user_genome_sizes = {}
    species_list = {}
    if user_sizes:
        logging.info(f"Reading user-provided genome sizes from {user_sizes}")
        with open(user_sizes, "r") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                cols = ["name", "taxid", "category", "expected_ungapped_length", "method_determined"]
                vals = line.strip().split("\t")
                taxid = vals[1]
                user_genome_sizes[vals[1]] = dict(zip(cols, vals))
                user_genome_sizes[vals[1]]["source"] = "user"
        logging.info(f"Found {len(user_genome_sizes)} user-provided genome size")

    # get the genome sizes from NCBI
    logging.debug("Getting latest genome sizes")
    genome_sizes = get_genome_sizes(outdir, ncbi_api_key, chunk_size, force)

    # Add user sizes to the genome sizes, only if they don't already exist
    # NCBI sizes will ALWAYS take precedence
    for taxid, genome in user_genome_sizes.items():
        if taxid not in genome_sizes:
            genome_sizes[taxid] = genome

    # Create species list to filter out of ATB
    for taxid, genome in genome_sizes.items():
        species_list[genome["name"]] = taxid
    logging.info(f"Found {len(species_list)} species from NCBI/User to filter from ATB")

    # Add ATB sizes to the genome sizes, only if they don't already exist
    # NCBI sizes and user sizes will ALWAYS take precedence
    logging.debug("Getting assembly sizes from ATB")
    atb_file_list = download_atb_file(
        f"{str(outdir)}/file_list.all.latest.tsv.gz",
        atb_file_list_url,
        progress=False if silent else True,
    )
    atb_assembly_stats = download_atb_file(
        f"{str(outdir)}/assembly-stats.tsv.gz",
        atb_assembly_stats_url,
        progress=False if silent else True,
    )

    # Parse the ATB file list
    logging.info(f"Parsing ATB file list: {atb_file_list}")
    samples, archives, species = parse_atb_file_list(atb_file_list)
    assembly_stats = parse_assembly_stats(atb_assembly_stats)

    # Capture ATB sizes for species that don't already have a size
    atb_species = {}
    for name, samples in species.items():
        if name not in species_list:
            if "_" not in name or not any(i.isdigit() for i in name):
                if len(samples) >= min_genomes:
                    atb_species[name] = samples
            else:
                logging.debug(f"Skipping {name} due to underscore or digit in name")

    species_taxids = species2taxid(list(atb_species.keys()), ncbi_api_key, chunk_size)
    for name, samples in atb_species.items():
        if name in species_taxids:
            taxid = species_taxids[name]
            genome_sizes[taxid] = {
                "name": name,
                "taxid": taxid,
                "category": "bacteria",
                "expected_ungapped_length": int(mean([int(assembly_stats[sample]["total_length"]) for sample in samples])),
                "source": "atb",
                "method_determined": f"Average assembly size of {len(samples)} AllTheBacteria samples",
            }

    # Write the genome sizes to a file
    logging.info(f"Writing genome sizes to {outdir}/sizemeup-sizes.txt")
    with open(f"{outdir}/sizemeup-sizes.txt", "w") as f:
        f.write(f"# sizemeup-build {datetime.datetime.now().strftime('%Y.%m.%d')}\n")
        f.write("name\ttax_id\tcategory\tsize\tsource\tmethod\n")
        for taxid, genome in genome_sizes.items():
            f.write(f"{genome['name']}\t{taxid}\t{genome['category']}\t{genome['expected_ungapped_length']}\t{genome['source']}\t{genome['method_determined']}\n")


def main():
    if len(sys.argv) == 1:
        sizemeup_build.main(["--help"])
    else:
        sizemeup_build()


if __name__ == "__main__":
    main()
