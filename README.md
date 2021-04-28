# ArcGIS Online Data Admin

This project is an evolving collection of scripts that can be used to manage public facing datasets used for demonstration purposes. The file/directory system is designed to be modular and thus reusable.

<!-- MDTOC maxdepth:6 firsth1:0 numbering:0 flatten:0 bullets:1 updateOnSave:1 -->

- [Environment](#environment)   
   - [Setup](#setup)   
      - [Conda Virtual Environment](#conda-virtual-environment)   
         - [Create](#create)   
         - [Activate](#activate)   
         - [Contribute](#contribute)   
      - [AGOL Credentials](#agol-credentials)   
         - [1. Config File -> Environment](#1-config-file-environment)   
         - [2. Arguments -> Environment](#2-arguments-environment)   
         - [Environment Credentials](#environment-credentials)   
      - [Logger](#logger)   
         - [Verbose](#verbose)   
         - [Output](#output)   
      - [Dev](#dev)   
- [Scripts](#scripts)   
   - [`transmute`](#transmute)   

<!-- /MDTOC -->

## Environment

This project is authored using `Python 3.8.5` managed by `Conda` and requires `arcgis`.

### Setup

Clone this repo and `cd` into this directory (`arcgis-online-data-admin`).

#### Conda Virtual Environment

> Prereq: [Install Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

It is recommended you use `conda` to create and manage the virtual environment.

##### Create

Create a Python 3 virtual environment and install project dependencies:

`conda env create -f afd-env.yml`

##### Activate

Then, activate the Python 3 virtual environment.

`conda activate afd-env`

> To deactivate the virtual environment type `conda deactivate`.

##### Contribute

If your contribution requires a new python dependency, please continue to use conda.

> Consult the [cheat sheet](https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf) for quick conda onboarding.

`conda install <channel?> <dependency>`

Be sure to export the new environment so that all contributors have the same environment.

`conda env export -c esri --from-history > afd-env.yml`

Other contributors will update their environment.

`conda env update -f afd-env.yml`

#### AGOL Credentials

Some aspects of this project (will) require AGOL credentials. The ArcGIS API for Python requires case-sensitive supplied username and password. There are two avenues through which you can supply AGOL username and password.

##### 1. Config File -> Environment

Some programs will ask for credentials via a `yml` configuration file. This configuration file should support the `portal` attribute at the highest level. If credentials are not supplied via configuration file, the program will fallback to read credentials from the environment. If the program cannot find credentials in either location, an exception is raised. For programs that follow this paradigm, the supplied `yml` configuration file must support a `portal` attribute at the highest level:

```yml
portal:
  # url is required
  url: https://www.arcgis.com
  # username is optional, omit this attribute to fallback to the environment
  username: your-username
  # password is optional, omit this attribute to fallback to the environment
  password: your-password
```

##### 2. Arguments -> Environment

Some programs will ask for credentials via command line arguments. If credentials are not supplied via command line, the program will fallback to read credentials from the environment. If the program cannot find credentials in either location, an exception is raised. For programs that follow this paradigm, arguments can be supplied using:

- `-u --username`
- `-p --password`

##### Environment Credentials

You can specify your AGOL credentials via your environment. These environment variable names are:

- `AFD_PORTAL_USERNAME`
- `AFD_PORTAL_PASSWORD`

*It's recommended you set credentials to your environment for one-and-done credential management.*

#### Logger

Some scripts will use a logger. The logger outputs script logs to console and optionally to a file path. The hierarchy of script log levels follows this pattern:

> DEBUG > INFO > WARNING > ERROR > CRITICAL

These scripts supply two optional command line arguments:

##### Verbose

`-v --verbose`

Print `DEBUG` level script logs to console. The default is `INFO`.

##### Output

`-o --output`

Write `DEBUG` level script logs to a file path.

> Run `tail -f output.log` to follow the output in a separate terminal session.

#### Dev

`-d --dev`

Some scripts support 'DEV' environment which allows you to pass a limit to how many records are processed by the script, reducing the run time of potentially long-running scripts.

## Scripts

### `transmute`

Transmute allows you to transmute data stored in a source feature layer to a destination feature layer. This is particularly useful for performing nightly data scrubbing tasks. 

The script uses the source data as the source of truth and edits the destination feature layer based on what is contained by the source. Any edits made to the source layer will be captured by the script and supplied to the destination layer at the next time the script is performed.

The script is designed to transmute a single feature layer, not an entire service; to transmute an entire service, perform the script repeatedly, layer by layer. 

The script takes a configuration file formatted as so.

```yaml
portal:
  url: http://www.arcgis.com
source:
  feature-service-item-id: "ITEM_ID"
  layer-index: 0
destination:
  feature-service-item-id: "ITEM_ID"
  layer-index: 0
  reference-id-key: "ATTRIBUTE_NAME"
```

The schemas for source and destination datasets must be compatible and are based on this simple equation,

```txt
destination.fields = source.fields + reference-id-key
```

The `reference-id-key` is a required field on the destination layer and is used to reference the contents of the destination layer to its source counterpart. The reference id key must be an Integer attribute field and can be named whatever you'd like.

You can test this script using the `testing-dataset` scheme.


```sh
python3 transmute.py -c ./schemes/testing-dataset.yml
```

> Note, the datasets are hosted in the **arcgisruntime** org.

#### Setting up your own transmutable services

Follow these steps to setup your own transmute.

1. Create a feature service in AGOL by uploading a Shapefile.
1. Create a second feature service in AGOL by uploading the same Shapefile.
1. You are welcome to drop some fields but be sure to drop them on both feature layers.
1. On the destination layer, add an Integer field for referencing the source datum.
1. Enable data collection setting on the destination layer.
1. Set sharing on the destination layer to public.
1. Set sharing on the source layer to private or organization.
1. Enable editing for both feature services.
1. Perform the script.