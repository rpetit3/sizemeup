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
                "--query",
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
    "--query",
    "-q",
    required=True,
    help="The species name or taxid to determine the size of",
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
    query: str,
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

    # Final Output
    final_output = {
        "name": "UNKNOWN_SPECIES",
        "tax_id": "UNKNOWN_TAXID",
        "category": "UNKNOWN_CATEGORY",
        "size": "0",
        "source": "UNKNOWN_SOURCE",
        "method": "UNKNOWN_METHOD",
    }

    final_query = query
    if Path(sizes).exists():
        genome_sizes, taxid2name, version = parse_sizes_file(sizes)
        lc_species = None
        if query.isdigit():
            if query in taxid2name:
                lc_species = taxid2name[query].lower()
        elif Path(query).is_file():
            """
            This is meant to be used with Bactopia's '*.bracken.classification.txt' file.

            It a two line TSV file with headers ('name','classification'), and we will use
            the 'classification' column from line 2 as the query.
            """
            logging.debug(f"Extracting query from {query}")
            with open(query, "r") as f:
                f.readline()
                final_query = f.readline().strip().split("\t")[1]
                lc_species = final_query.lower()
        else:
            lc_species = query.lower()

        logging.debug(f"Querying for {lc_species}")
        if lc_species in genome_sizes:
            species = genome_sizes[lc_species]["name"]
            logging.info(f"Found the size of {species} in the sizes file")
            logging.info(genome_sizes[lc_species])

            final_output['name'] = species
            final_output['tax_id'] = genome_sizes[lc_species]["tax_id"]
            final_output['category'] = genome_sizes[lc_species]["category"]
            final_output['size'] = genome_sizes[lc_species]["size"]
            final_output['source'] = genome_sizes[lc_species]["source"]
            final_output['method'] = genome_sizes[lc_species]["method"]
        else:
            if query.isdigit():
                logging.error(f"Could not find the taxid '{final_query}' in the sizes file, please consider creating an issue at https://github.com/rpetit3/sizemeup/issues to report this")
            else:
                logging.error(f"Could not find '{final_query}' in the sizes file, please consider creating an issue at https://github.com/rpetit3/sizemeup/issues to report this")
    else:
        logging.error(f"Could not find the sizes file {sizes}")
        sys.exit(1)

    # Create a table to display the genome sizes
    table = Table(title="Query Result")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("TaxID", style="magenta")
    table.add_column("Category", style="red")
    table.add_column("Size", style="green")
    table.add_column("Source", style="blue")
    table.add_column("Method", style="yellow")

    table.add_row(
        final_output["name"],
        final_output["tax_id"],
        final_output["category"],
        final_output["size"],
        final_output["source"],
        final_output["method"],
    )

    print(table)

    # write the genome size to a file
    # Create the output directory
    logging.debug(f"Creating output directory: {outdir}")
    Path(outdir).mkdir(parents=True, exist_ok=True)

    print(f"Writing the genome size to {outdir}/{prefix}-sizemeup.txt")
    with open(f"{outdir}/{prefix}-sizemeup.txt", "w") as f:
        cols = ["name", "tax_id", "category", "size", "source", "method"]
        vals = [final_output[col] for col in cols]
        f.write("\t".join(cols) + "\n")
        f.write("\t".join(vals) + "\n")


def main():
    if len(sys.argv) == 1:
        sizemeup.main(["--help"])
    else:
        sizemeup()


if __name__ == "__main__":
    main()
