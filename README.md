# Measuring Effects of Analyst Characteristics On Forecast Accuracy 

## Introduction

### Project Setup with Poetry
#### Prerequisites
- Python 3.x installed on your system
- Access to a terminal or command prompt

#### Step 1 - Poetry Installation
```bash
pip install poetry
```
#### Step – Clone the repository
First, you need to navigate to a folder where the repo will be cloned, and then clone it.

```bash
cd path/to/folder

git clone https://github.com/moshchev/gsfm_SS24.git
```
#### Step 3 - Setting up the Environment
Navigate inside of the repo and install poetry environment

*Note: the poetry env will be installed inside of poetry directory. If you want to have env installed inside of the repo you can modify it with the second line of code in the next block.*

```bash
cd path/to/folder/gsfm_SS24

poetry config virtualenvs.in-project true

poetry install
```

#### Step 4 - Run scripts
**python scripts**

To run a python script you can just say

```bash
poetry run script.py
```
or you can spawn a poetry shell and run scripts like in a normal venv

```bash
poetry shell
python script.py
```

**jupyter notebooks**

To run a notebook you need to create a jupyter server.
``` bash
poetry run jupyter notebook
```

## Model specification

__Draft__: (TBD)
$$Acc_{ijt} = \alpha[i] + \beta_{TOP10} * TOP10_{ijt}  + \beta_{BCOV} * BCOV_{ijt} + \beta_{EXP} * EXP_{ijt} + \beta_{SURP} * SURP_{ijt} + \beta_{PCOM} * PCOM_{}$$

where,
- $ACC_{ijt}$: Proportional Mean Absolute Forecast Error (PMAFE) of analyst i forecast for company j in fiscal year t
- $BRKZ_{it}$: Number of analysts working at the broker in year t
- $TOP10_{ijt}$: Dummy variable set to 1 if analyst i works at a brokerage that is in the top decile during fiscal year t, and 0 otherwise (size by number of analysts at i's brokerage that issued forecasts)
- $HORZ_{ijt}$: Mean forecast horizon of all of analyst i's issued forecast within one fiscal period t
- $FOLLW_{ijt}$: Number of analysts following the same company j as analyst i in fiscal year t 
- $BCOV_{ijt}$: Coverage as number of analysts at analyst i's brokerage following company j in year t
- $EXP_{ijt}$: Experience of analyst i as number of forecasts issued till current fiscal year t
- $SURP_{ijt}$: Previous year mean surprise of analyst i issued forecasts for company j in fiscal year t-1
- $SURPLA_{ijt}$: Lagged surprise by one period
- $PCOM_{ijt}$: Portfolio complexity of analyst i, as the number of distinct industries followed in year t
- $COMP_{it}$: Number of companies followed by analyst i in fiscal year t

## Data Sources and Data Guides

| Data Source | Link |
|-------------|------|
| IBES Detail Analyst Forecasts and Actuals | [Link](https://wrds-www.wharton.upenn.edu/pages/get-data/ibes-thomson-reuters/ibes-academic/detail-history/actuals/) |
| SIC Industry Codes | [Link](https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/?saved_query=4009719) |
| WRDS Python Package | [Link](https://wrds-www.wharton.upenn.edu/documents/1443/wrds_connection.html) |
| Linking IBES and CRSP Data (Python)|[Link](https://wrds-www.wharton.upenn.edu/pages/wrds-research/applications/python-replications/linking-ibes-and-crsp-data-python/)|
|IBES CRSP Link|[Link](https://wrds-www.wharton.upenn.edu/pages/get-data/linking-suite-wrds/ibes-crsp-link/)|
| IBES Detail History Data Guide | [Link](https://wrds-www.wharton.upenn.edu/documents/495/IBES_Detail_History_User_Guide_-_December_2016.pdf) |
| IBES Summary History Data Guide | [Link](https://wrds-www.wharton.upenn.edu/documents/505/IBES_Summary_History_User_Guide_-_March_2013.pdf) |


## Contributors
- Alexander Moshchev
- Kay Simon
- Marius Gnoth
- Bastian Schmidt
- Jialiang Gao
