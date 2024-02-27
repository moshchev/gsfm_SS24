import pandas as pd
import numpy as np




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


def preprocessing(df):
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
    
    df_forecasts = df.rename_columns(df_forecasts)
    
    return df_forecasts


