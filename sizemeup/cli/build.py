import sys

import rich
import rich.console
import rich.traceback
import rich_click as click
from rich import print
from rich.logging import RichHandler
from rich.table import Table

import pandas as pd

import sizenmeup

NCBI_GENOME_SIZE_URL = (
    "https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/species_genome_size.txt.gz"
)

NCBI_TAXDUMP_URL = (
    "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
)

# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "sizemeup-build": [
        {
            "name": "Additional Options",
            "options": [
                "--version",
                "--help",
            ],
        },
    ]
}


@click.command()
@click.version_option(sizemeup.__version__, "--version", "-V")
def sizemeup():
    """sizemeup-build - Build the taxid and species genome sizes from NCBI"""

    print("sizemeup - A simple tool to determine the genome size of an organism")


def main():
    if len(sys.argv) == 1:
        sizemeup.main(["--help"])
    else:
        sizemeup()


if __name__ == "__main__":
    main()
