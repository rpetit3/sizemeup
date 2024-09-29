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
from sizemeup.utils import parse_sizes_file

# Set up Rich
stderr = rich.console.Console(stderr=True)
rich.traceback.install(console=stderr, width=200, word_wrap=True, extra_lines=1)
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.OPTION_GROUPS = {
    "sizemeup": [
        {
            "name": "Required Options",
            "options": [
                "--species",
                "--sizes",
            ],
        },
        {
            "name": "Additional Options",
            "options": [
                "--outdir",
                "--prefix",
                "--silent",
                "--verbose",
                "--version",
                "--help",
            ],
        },
    ]
}


@click.command()
@click.version_option(sizemeup.__version__, "--version", "-V")
@click.option(
    "--species",
    "-s",
    required=True,
    help="The species to determine the size of",
)
@click.option(
    "--sizes",
    "-z",
    required=True,
    default=os.environ.get("SIZEMEUP_SIZES", None),
    show_default=True,
    help="The built in sizes file to use",
)
@click.option(
    "--outdir",
    "-o",
    type=click.Path(exists=False),
    default="./",
    show_default=True,
    help="Directory to write output",
)
@click.option(
    "--prefix",
    "-p",
    type=str,
    default="sizemeup",
    show_default=True,
    help="Prefix to use for output files",
)
@click.option("--silent", is_flag=True, help="Only critical errors will be printed")
@click.option("--verbose", is_flag=True, help="Increase the verbosity of output")
def sizemeup(
    species: str,
    sizes: str,
    outdir: str,
    prefix: str,
    silent: bool,
    verbose: bool,
):
    """sizemeup - A simple tool to determine the genome size of an organism"""

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

    if Path(sizes).exists():
        genome_sizes, version = parse_sizes_file(sizes)
        lc_species = species.lower()
        if lc_species in genome_sizes:
            logging.info(f"Found the size of {species} in the sizes file")
            logging.info(genome_sizes[lc_species])

            # Create a table to display the genome sizes
            table = Table(title="Query Result")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("TaxID", style="magenta")
            table.add_column("Size", style="green")
            table.add_column("Source", style="blue")
            table.add_column("Method", style="yellow")

            table.add_row(
                species,
                genome_sizes[lc_species]["tax_id"],
                genome_sizes[lc_species]["size"],
                genome_sizes[lc_species]["source"],
                genome_sizes[lc_species]["method"],
            )

            print(table)

            # write the genome size to a file
            # Create the output directory
            logging.debug(f"Creating output directory: {outdir}")
            Path(outdir).mkdir(parents=True, exist_ok=True)

            print(f"Writing the genome size to {outdir}/{prefix}-sizemeup.txt")
            with open(f"{outdir}/{prefix}-sizemeup.txt", "w") as f:
                cols = ["name", "tax_id", "size", "source", "method"]
                vals = [genome_sizes[lc_species][col] for col in cols]
                f.write("\t".join(cols) + "\n")
                f.write("\t".join(vals) + "\n")
        else:
            logging.error(f"""Could not find '{species}' in the sizes file, please consider creating an issue at https://github.com/rpetit3/sizemeup/issues to report this""")
    else:
        logging.error(f"Could not find the sizes file {sizes}")
        sys.exit(1)

def main():
    if len(sys.argv) == 1:
        sizemeup.main(["--help"])
    else:
        sizemeup()


if __name__ == "__main__":
    main()
