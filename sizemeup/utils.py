import logging

def parse_sizes_file(sizes_file: str) -> list:
    """
    Parse the sizes file into a dictionary

    Example sizes file:
    ```
    # sizemeup-build 2024.09.29
    name	tax_id	size	source	method
    Azorhizobium caulinodans	7	5636513	ncbi	automatic
    Buchnera aphidicola	9	559368	ncbi	automatic
    Shewanella colwelliana	23	4631520	ncbi	automatic
    Shewanella putrefaciens	24	4386283	ncbi	automatic
    ```

    The first line is a version line that starts with a `#`.
    The second line is the column names.
    The rest of the lines are the data.

    Args:
        sizes_file (str): The path to the sizes file

    Returns:
        list: A list containing the genome sizes dictionary and the version string
    """
    genome_sizes = {}
    taxid2name = {}
    version = None
    col_names = None

    logging.info(f"Reading genome sizes from {sizes_file}")
    with open(sizes_file, "r") as f:
        for line in f:
            if line.startswith("#"):
                version = line.strip(). split(" ")[-1]
            elif line.startswith("name"):
                col_names = line.strip().split("\t")
            else:
                vals = line.strip().split("\t")
                row = dict(zip(col_names, vals))
                genome_sizes[row["name"].lower()] = row
                taxid2name[row["tax_id"]] = row["name"]

    return [genome_sizes, taxid2name, version]
