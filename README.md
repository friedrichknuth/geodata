# dataquery
Python library and client for public geospatial data retrieval


## Installation

Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)  

After installing Miniconda set up [Mamba](https://mamba.readthedocs.io/en/latest/installation.html) (optional but recommended)
```
$ conda install mamba -n base -c conda-forge
```
Clone the repo and set up the conda environment  

```
$ git clone https://github.com/friedrichknuth/dataquery.git
$ cd ./dataquery
$ mamba env create -f environment.yml
$ conda activate dataquery
$ pip install .
```

## Usage

### From Command Line

```
# Download 3DEP DSM from Planetary Computer

import dataquery as dq

dq.dems.download_planetary_3DEP_DSM(
    collection="3dep-lidar-dsm",
    bbox=[-121.846, 48.7, -121.823, 48.76],
    time_range="2000-12-01/2020-12-31",
    output_folder="downloads",
    overwrite=True,
)

```

### From Command Line

```
# Download 3DEP DSM from Planetary Computer

download_3DEP_DSM --collection 3dep-lidar-dsm \
                  --bbox '-121.846 48.7 -121.823 48.76' \
                  --time-range 2000-12-01/2020-12-31 \
                  --output-folder downloads
                  --overwrite

```