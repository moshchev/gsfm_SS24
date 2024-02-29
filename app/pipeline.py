import pandas as pd
import numpy as np


#### LOAD DATASETS ####

def load_datasets():
    """
    Loads the datasets required for the pipeline.

    Returns:
    df_forecasts (pandas.DataFrame): DataFrame containing the IBES forecasts data.
    df_company (pandas.DataFrame): DataFrame containing the company data.
    """
    file_path_ibes = "../data/dataset2014-2022-v4.zip"
    file_path_sic = "data/dataset-company-industry-data-v1.csv"
    df_forecasts = pd.read_csv(file_path_ibes)
    df_company = pd.read_csv(file_path_sic)
    
    return df_forecasts, df_company


#### PREPROCESSING FUNCTIONS ####

def preprocessing_ibes(df):
    """
    Preprocesses the input DataFrame by performing the following steps:
    1. Lowercase column names.
    2. Drop specified columns.
    3. Convert specified columns to datetime format.
    4. Filter forecasts based on a specific period.
    5. Rename columns.

    Args:
        df (pandas.DataFrame): Input DataFrame containing the data to be preprocessed.

    Returns:
        pandas.DataFrame: Preprocessed DataFrame.
    """
    
    # lower case column names
    df_forecasts = df.rename(columns={col: col.lower() for col in df_forecasts.columns})
    
    # drop columns
    columns_to_drop = ["fpi","measure","cusip"]
    df_forecasts = df_forecasts.drop(columns=columns_to_drop)
    
    df_forecasts = df_forecasts.dropna(subset=['actual_eps'])
    df_forecasts = df_forecasts.dropna(subset=['estimated_eps'])
    
    
    def convert_to_datetime(df):
        columns_to_convert = ['fpedats','revdats', "anndats", 'anndats_act']
        for column in columns_to_convert:
            df[column] = pd.to_datetime(df[column])
            return df
    
    df_forecasts = convert_to_datetime(df_forecasts)
    
    def filter_forecasts_period(df):
        df['difference_date'] = df['fpedats'] - df['anndats']
        df = df[(df['difference_date']> pd.Timedelta(days=30))&(df['difference_date']<pd.Timedelta(days=365))]
        return df
    
    df_forecasts = filter_forecasts_period(df_forecasts)
    
    def rename_columns(df):
        df_forecasts = df.rename(columns={"ticker": "ibes_ticker_pk", "oftic": "official_ticker", "analys": "analyst", 
                                  "value": "estimated_eps", "fpedats": "fiscal_period_ending", 
                                  "revdats": "revision_date", "anndats": "announce_date", 
                                  "actual": "actual_eps", "anndats_act": "announce_date_actual",
                                  "difference_date": "forecast_horizon"})
        return df_forecasts
    
    df_forecasts = rename_columns(df_forecasts)
    
    return df_forecasts


def preprocessing_compustat(df):
    # reduce to highest level of SIC code
    df.loc[df['sic'].isna(), 'sic'] = -1 
    df['sic'] = df['sic'].astype(str).str[:2]
    df['sic'] = df['sic'].astype('int')
    
    
#### ADD DV AND FEATURE FUNCTIONS ####

def calculate_pmafe(df):
    """
    This function first calculates the absolute forecast error for each analyst i forecast of firm j in year t
    If analyst i has multiple forecasts for firm j in year t, the function calculates the average forecast error
    In the second step an extra column is calculated for the overall forecast error is calculate for each firm j in year t
    In the third step, the function calculates the PMAFE for each analyst i forecast of firm j in year t
    This function adds new columns to the dataframe:
    - afe_analyst_i: the absolute forecast error for each analyst i forecast of firm j in year t
    - afe_analyst_i_avg: the average absolute forecast error for each analyst i forecast of firm j in year t
    - afe_mean_firm_j: the overall forecast error for each firm j in year t
    - pmafe: the PMAFE for each analyst i forecast of firm j in year t
    """
    # Step 1: Calculate the average absolute forecast error for each analyst i forecast of firm j in year t
    df['afe_analyst_i'] = np.abs(df['estimated_eps'] - df['actual_eps'])
    
    df_grouped = df.groupby(['ibes_ticker_pk', 'analyst', 'fiscal_period_ending']).agg({'afe_analyst_i': 'mean'}).reset_index()
    df_grouped = df_grouped.rename(columns={'afe_analyst_i': 'afe_analyst_i_avg'})
    df = pd.merge(df, df_grouped, on=['ibes_ticker_pk', 'analyst', 'fiscal_period_ending'], how='left')
    
    # Step 2: Calculate the overall forecast error for each firm j in year t
    df['afe_mean_firm_j'] = df.groupby(["ibes_ticker_pk", "fiscal_period_ending"])["afe_analyst_i"].transform("mean")
    
    # Step 3: Calculate the PMAFE for each analyst i forecast of firm j in year t
    df['pmafe'] = (df['afe_analyst_i_avg'] - df['afe_mean_firm_j']) / df['afe_mean_firm_j']
    
    return df








#### COLLAPSE DATA ####

def collapse_processed_df(df):
    """_summary_
    This function collapses the input df into the final df so that one row should correspond to one analyst 
    i's forecast of firm j in fiscal year t with accuracy measure pmafe and other relevant features
    """




#### DATA SCIENCE FUNCTIONS ####


