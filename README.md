[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-908a85?logo=gitpod)](https://gitpod.io/#https://github.com/rpetit3/sizemeup)

# `sizemeup`

`sizemeup` is a simple tool to retrieve the genome size for a given species name or tax ID. It utilizes
known genome sizes available from [NCBI's Assembly Reports](https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/README_species_genome_size.txt)
in combination with user provided genome sizes that may not be available from NCBI.

## Contributing

If you have a species of interest that is not available in the NCBI Assembly Reports, please
consider submitting an issue so that we can get it added to `sizemeup`. Otherwise, if you have
ideas to improve `sizemeup` please feel free to!

## Installation

You can install `sizemeup` using `conda`:

```bash
conda create -n sizemeup -c conda-forge -c bioconda sizemeup
conda activate sizemeup
sizemeup --help
```

## Available Commands

### `sizemeup`

`sizemeup` is the main tool that outputs the known genome size for a given species name or tax ID.

#### Usage

```bash
sizemeup --help

 Usage: sizemeup [OPTIONS]

 sizemeup - A simple tool to determine the genome size of an organism

╭─ Required Options ────────────────────────────────────────────────────────────────────╮
│ *  --query    -q  TEXT  The species name or taxid to determine the size of [required] │
│ *  --sizes    -z  TEXT  The built in sizes file to use [required]                     │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Additional Options ──────────────────────────────────────────────────────────────────╮
│ --outdir   -o  PATH  Directory to write output [default: ./]                          │
│ --prefix   -p  TEXT  Prefix to use for output files [default: sizemeup]               │
│ --silent             Only critical errors will be printed                             │
│ --verbose            Increase the verbosity of output                                 │
│ --version  -V        Show the version and exit.                                       │
│ --help               Show this message and exit.                                      │
╰───────────────────────────────────────────────────────────────────────────────────────╯
```

#### Example

```bash
sizemeup --query "Staphylococcus aureus" --silent
                                 Query Result                                 
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name                  ┃ TaxID ┃ Category ┃ Size    ┃ Source ┃ Method       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Staphylococcus aureus │ 1280  │ bacteria │ 2800000 │ ncbi   │ manually-set │
└───────────────────────┴───────┴──────────┴─────────┴────────┴──────────────┘
Writing the genome size to .//sizemeup-sizemeup.txt

sizemeup --query 1280 --silent
                                 Query Result                                 
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Name                  ┃ TaxID ┃ Category ┃ Size    ┃ Source ┃ Method       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Staphylococcus aureus │ 1280  │ bacteria │ 2800000 │ ncbi   │ manually-set │
└───────────────────────┴───────┴──────────┴─────────┴────────┴──────────────┘
Writing the genome size to .//sizemeup-sizemeup.txt
```

If the `--query` value is found a table is printed to STDOUT as well as to a file named
`{PREFIX}-sizemeup.txt` where `{PREFIX}` is the value of the `--prefix` option (_default sizemeup_).

Here is an example of the output file:

```tsv
name	tax_id	category	size	source	method
Staphylococcus aureus	1280	bacteria	2800000	ncbi	manually-set
```

However is a species is not found, the you get the following output:

```bash
sizemeup --query "escherichia colis" --silent
2024-09-29 20:24:17 ERROR    2024-09-29 20:24:17:root:ERROR - Could not find 'escherichia colis' in the sizes file,      sizemeup.py:138
                             please consider creating an issue at https://github.com/rpetit3/sizemeup/issues to report
                             this
                                         Query Result
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Name            ┃ TaxID         ┃ Category         ┃ Size ┃ Source         ┃ Method         ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ UNKNOWN_SPECIES │ UNKNOWN_TAXID │ UNKNOWN_CATEGORY │ 0    │ UNKNOWN_SOURCE │ UNKNOWN_METHOD │
└─────────────────┴───────────────┴──────────────────┴──────┴────────────────┴────────────────┘
Writing the genome size to .//sizemeup-sizemeup.txt
```

### `sizemeup-build`

`sizemup-build` is a helper tool used to build the genome size database for `sizemeup`. Do do
this it:

1. Downloads the latest NCBI Assembly Reports
2. Determines species names based on tax id using NCBI Datasets API
3. Merges any user provided genome sizes not available from NCBI
4. Add assembly sizes from [ATB](https://allthebacteria.readthedocs.io/en/latest/) with sufficient representation
5. Writes the genome sizes to a TSV file

**Note**: This tool isn't necessary for most users, just a simple way to update the database
on your own or at new releases of `sizemeup`.

In the end, it produces a TSV file with the following columns:

- `name` - the species name
- `tax_id` - the NCBI tax id
- `category` - the category of the species (e.g. `bacteria`, `virus`)
- `size` - the genome size in base pairs
- `source` - the source of the genome size (e.g. `ncbi`, `user`)
- `method` - the method used to determine the genome size (e.g. `automatic`, `manual`)

## Citing `sizemeup`
If you make use of `sizemeup` in your analysis, please cite the following:

- __sizemeup__  
_Petit III RA, Fearing T, Rowley, C [sizemeup: A simple tool to determine the genome size of an organism](https://github.com/rpetit3/sizemeup) (GitHub)_  

_ __AllTheBacteria__  
_Hunt M., Lima L., Shen W., Lees J., Iqbal Z. [AllTheBacteria - all bacterial genomes assembled, available and searchable](https://doi.org/10.1101/2024.03.08.584059) bioRxiv 2024.03.08.584059_  

## Motivation and Naming

Talking with Taylor, we have a workflow in [Bactopia](https://bactopia.github.io/latest/) called
`teton` for human read scrubbing and taxonomic classification. After running `teton`, the idea
was to run Bactopia to analyze the samples. However, Bactopia requires a genome size for each
sample in order to calculate coverage and a few other metrics. Sure, we could manually look up
the genome size for each sample, that would be tedious and time consuming. We decided to develop
`sizemeup` to handle the looking up genome sizes for us. In addition this paves the way for
users of Bactopia to use `teton` + `sizemeup` to easily mix species within their runs. In other
words, `sizemeup` was built to support the Bactopia workflow (_but you can use it for whatever!_).

As for the name, I wanted something fun and catchy. It's a simple tool to retrieve the genome
size of a given species name, so, I thought "sizemeup" would work!

## Funding

Support for this project came (in part) from the [Wyoming Public Health Division](https://health.wyo.gov/publichealth/).

![Wyoming Public Health Division](data/assets/wyphd-banner.jpg)
