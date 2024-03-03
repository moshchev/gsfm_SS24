# Measuring Effects of Analyst Characteristics On Forecast Accuracy 

## Introduction

_How to use the repo_

## Model specification

__Draft__:
$$ACC_{ijt} = \alpha[i] + \beta_{TOPB} * TOPB_{ijt}  + \beta_{BCOV} * BCOV_{ijt} + \beta_{EXP} * EXP_{ijt} + \beta_{SURP} * SURP_{ijt} + \beta_{PCOM} * PCOM_{}$$

where,
- $ACC_{ijt}$: Proportional Mean Absolute Forecast Error (PMAFE) of analyst i forecast for company j in fiscal year t
- $TOPB_{ijt}$: Dummy variable set to 1 if analyst i works at a brokerage that is in the top decile during year t, and 0 otherwise (size by number of analysts at i's brokerage that issued forecasts)
- $BCOV_{ijt}$: Coverage as number of analysts at analyst i's brokerage following company j in year t
- $EXP_{ijt}$: Experience of analyst i as number of forecasts issued till current fiscal year t
- $SURP_{ijt}$: Previous year mean surprise of analyst i issued forecasts for company j in fiscal year t-1 (lag feature)
- $PCOM_{ijt}$: Portfolio complexity of analyst i, as the number of distinct companies j / industries followed in year t
- ...

## Data Sources and Data Guides

| Data Source | Link |
|-------------|------|
| IBES Detail Analyst Forecasts and Actuals | [Link](https://wrds-www.wharton.upenn.edu/pages/get-data/ibes-thomson-reuters/ibes-academic/detail-history/actuals/) |
| SIC Industry Codes | [Link](https://wrds-www.wharton.upenn.edu/pages/get-data/compustat-capital-iq-standard-poors/compustat/north-america-daily/fundamentals-annual/?saved_query=4009719) |
| WRDS Python Package | [link](https://wrds-www.wharton.upenn.edu/documents/1443/wrds_connection.html) |
| IBES Detail History Data Guide | [Link](https://wrds-www.wharton.upenn.edu/documents/495/IBES_Detail_History_User_Guide_-_December_2016.pdf) |
| IBES Summary History Data Guide | [Link](https://wrds-www.wharton.upenn.edu/documents/505/IBES_Summary_History_User_Guide_-_March_2013.pdf) |


## Contributors
- Alexander Moshchev
- Kay Simon
- Marius Gnoth
- Bastian Schmidt
- Jialiang Gao
