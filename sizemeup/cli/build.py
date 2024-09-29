import datetime
import logging
import os
import sys
from pathlib import Path

import rich
import rich.console
import rich.traceback
import rich_click as click
from rich import print
from rich.logging import RichHandler
from rich.table import Table

import sizemeup
from sizemeup.ncbi import get_genome_sizes


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
    default=200,
    help="The size of the chunks to split the list into",
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
    if user_sizes:
        logging.info(f"Reading user-provided genome sizes from {user_sizes}")
        with open(user_sizes, "r") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                cols = ["name", "taxid", "expected_ungapped_length", "method_determined"]
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

    # Write the genome sizes to a file
    logging.info(f"Writing genome sizes to {outdir}/sizemeup-sizes.txt")
    with open(f"{outdir}/sizemeup-sizes.txt", "w") as f:
        f.write(f"# sizemeup-build {datetime.datetime.now().strftime('%Y.%m.%d')}")
        f.write("name\ttax_id\tsize\tsource\tmethod\n")
        for taxid, genome in genome_sizes.items():
            f.write(f"{genome['name']}\t{taxid}\t{genome['expected_ungapped_length']}\t{genome['source']}\t{genome['method_determined']}\n")


def main():
    if len(sys.argv) == 1:
        sizemeup_build.main(["--help"])
    else:
        sizemeup_build()


if __name__ == "__main__":
    main()
