# Drift Modeling Tool

The container is intended for running simulations of marine object drift. The project is built on the **Python** library [OpenDrift](https://opendrift.github.io/).
As *input*, it accepts a JSON configuration file and datasets in GRIB or NetCDF format.
The *output* is a dataset containing movement trajectories, saved in NetCDF format.

# Project Structure
```
opendrift-container/
│
├── main.py                     # main program
├── config_verification.py      # JSON file validation and splitting into simulation and data configurations
├── case_study_tool.py          # functions for simulation and data preparation
│
├── DATA/
│   └── VariableMapping.json    # internal dictionary for correct parameter name mapping
│
├── INPUT/                      
│   └── input_test.json         # dummy configuration file for container testing
│
├── tests/                     
│   └── test_functions.py       # tests of main functions: configuration verification,
│                               # data preparation, and simulation execution correctness
│
├── requirements.txt            # required Python packages
├── Dockerfile                  # container configuration
├── .dockerignore               # files ignored by the container
├── .gitignore                  # files ignored by Git
└── README.md    
```
# Setup & Usage


-image building:

```docker build -t opendrift-container .```

-running the container:

```
docker run \
	-v path/to/host/dataset/folder:/DATASETS \
   	-v path/to/host/config/file.json:/opendrift-container/INPUT/config.json \
	-v path/to/store/results:/OUTPUT \
	opendrift_container python main.py config.json 
``` 
# Configuration File

All configuration attributes listed below must be collected in a single JSON file, for example: `config.json`.

## REQUIRED
- *model* – model type, one of: `OceanDrift`, `Leeway`, or `ShipDrift`. [`str`]
- *start_position* – starting position coordinates. A list of length 2, where the first element is `Latitude` and the second is `Longitude`.
  Latitude and longitude can be either `float` values or lists of `float`, but list lengths must match.
  If `"seed_type" = "cone"` is selected, each coordinate must consist of exactly two values (line start and end points). [`list`]
- *start_t* – start time readable by `pandas.to_datetime`, e.g. `2025-12-08 11:00:00`. [`str`]
- *end_t* – end time readable by `pandas.to_datetime`, e.g. `2025-12-31 12:00:00`. [`str`]

## DATA RELATED
- *vocabulary* – dictionary mapping parameter names from the dataset to standard CF names. [`dict`]
- *folder* – internal container directory (default `/DATASETS`) mapped to a host directory.
  Must contain GRIB or NetCDF files. [`str`]

### Optional
- *concatenation* – allow using subfolders and concatenate datasets per subfolder. Default `False`. [`bool`]
- *copernicus* – enable loading data from Copernicus Marine via API. Default `False`. [`bool`]
  - *border* – `[min_lat, max_lat, min_lon, max_lon]`, default `[54, 62, 13, 30]`. [`list`]
  - *user* – Copernicus Marine username. Credentials are not encrypted. [`str`]
  - *pword* – Copernicus Marine password. [`str`]

## SIMULATION
- *num* – number of simulated particles. Default `100`. [`int`]
- *seed_type* – `elements` or `cone`. Default `elements`. [`str`]
- *rad* – dispersion radius in meters.
  - For `elements`: integer or list matching coordinate lengths.
  - For `cone`: integer or list of two integers `[start_radius, end_radius]`.
  Default `0`. [`int`] or [`list[int]`]
- *backtracking* – enable backward simulation. Requires start time > end time and negative `time_step`. Default `False`. [`bool`]
- *time_step* – time step in seconds. Default `1800`. Negative only allowed for backtracking. [`int`]

## MODEL SETTINGS
- *wdf* – wind drift factor (0–1). Default `0.02`. [`float`]
- *lw_obj* – Leeway object ID (1–85). Default `1`. [`int`]
- *ship* – ship dimensions `[length, beam, height, draft]` in meters. Default `[62, 8, 10, 5]`. [`list`]
  - *orientation* – `left`, `right`, or `random`. Default `random`. [`str`]

## ADDITIONAL
- *configurations* – additional simulation configurations. [`dict`]
- *file_name* – output file name. Default `{model}_{start_time}_{now_time}.nc`. [`str`]
