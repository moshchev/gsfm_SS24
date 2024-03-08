import pandas as pd
import numpy as np


#### LOAD DATASETS ####

def load_datasets():
    """
    Loads the datasets required for the pipeline.

    Returns:
        df_forecasts (pandas.DataFrame): DataFrame containing the IBES forecasts data.
    """

    df_forecasts = pd.read_parquet('data/raw/ibes-forecasts.parquet')

    return df_forecasts


### Service functions
def convert_to_datetime(df):
    """
    Service function for changing columns to datetime format

    Args:
        df (pandas.DataFrame): Dataframe with defined columns to adjust

    Returns:
        df (pandas.DataFrame): processed dataframe
    """
    columns_to_convert = ['fpedats','revdats', 'anndats', 'anndats_act']
    for column in columns_to_convert:
        df[column] = pd.to_datetime(df[column])
        
    return df


#### PREPROCESSING FUNCTIONS ####

def preprocessing_ibes(df:pd.DataFrame):
    """
    Preprocesses the input DataFrame by performing the following steps:
    1. Lowercase column names.

    2. Drop specified columns.
        2.1 Delete rows with actual_eps = NAN or estimated_eps = NAN

    3. Convert specified columns to datetime format.

    4. Filter forecasts
        4.1 Include only forecasts issued no earlier than 1 year ahead and no later than 30 days before fiscal year end
            4.1.1. Compute mean of the horizon days
        4.2 Filter year of 2023, data is not complete

    5. Rename columns.

    6. Join preprocessed data

    Args:
        df (pandas.DataFrame): Input DataFrame containing the data to be preprocessed.

    Returns:
        pandas.DataFrame: Preprocessed DataFrame.
    """
    
    # #1 lower case column names
    df = df.rename(columns={col: col.lower() for col in df.columns})
    
    # #2 drop columns
    df = df.drop(columns=["fpi","measure","cusip"])
    df = df.dropna(subset=['actual'])
    df = df.dropna(subset=['value'])
    
    # #3 change format and add years
    df = convert_to_datetime(df)
    df['forecast_announce_year'] = df.anndats.dt.year
    df['fiscal_year'] = df.fpedats.dt.year

    # #4 Filter columns
    # 4.1 Include only forecasts issued no earlier than 1 year ahead and no later than 30 days before fiscal year end
    df['forecast_horizon'] = df['fpedats'] - df['anndats']
    df = df[(df['forecast_horizon']> pd.Timedelta(days=30))&(df['forecast_horizon']<pd.Timedelta(days=365))]
    # 4.1.1.  Calculate mean forecast horizon days
    df['mean_forecast_horizon_days'] = df.groupby(['analys','ticker','fpedats'])['forecast_horizon'].transform('mean')
    df['mean_forecast_horizon_days'] = df['mean_forecast_horizon_days'].dt.days

    # 4.2 Filter 2023
    df = df[df['fiscal_year'] != 2023]

    # #5 Rename columns
    df = df.rename(columns={"ticker": "ibes_ticker_pk", "oftic": "official_ticker", "analys": "analyst", 
                                "value": "estimated_eps", "fpedats": "fiscal_period_ending", 
                                "revdats": "revision_date", "anndats": "announce_date", 
                                "actual": "actual_eps", "anndats_act": "announce_date_actual", "cname":"company_name"
                                })

    return df

    
#### ADD DV AND FEATURE FUNCTIONS ####

def calculate_pmafe(df):
    """
    Calculates various forecast error metrics for analysts' forecasts of firms' earnings per share (EPS) and updates the input DataFrame with new columns related to these errors.

        The function performs the following steps:
        1. Calculates the Absolute Forecast Error (AFE) for each forecast by an analyst 'i' for a firm 'j' in year 't'. 
           If an analyst 'i' provides multiple forecasts for the same firm 'j' in year 't', the average of these forecasts' errors is calculated.
        2. Adds a column indicating the overall average forecast error for each firm 'j' in year 't', considering all analysts.
        3. Calculates the Proportional Mean Absolute Forecast Error (PMAFE) for each analyst 'i' for a firm 'j' in year 't', comparing individual analyst accuracy against the overall firm accuracy.
        4. Excludes forecasts for firms where only one analyst provided a forecast, to ensure the reliability of comparative error measurements.

        New Columns Added to DataFrame:
        - 'afe_analyst_i': Absolute Forecast Error for each forecast by an analyst 'i' for a firm 'j' in year 't'.
        - 'afe_analyst_ijt_mean': Average Absolute Forecast Error for an analyst 'i' for a firm 'j' in year 't'.
        - 'afe_firm_jt_mean': Overall average forecast error for each firm 'j' in year 't'.
        - 'pmafe': Proportional Mean Absolute Forecast Error for each forecast by an analyst 'i' for a firm 'j' in year 't'.

    Parameters:
        df (pd.DataFrame): A pandas DataFrame containing at least the columns 'estimated_eps', 'actual_eps', 'ibes_ticker_pk', 'analyst', and 'fiscal_period_ending'.

    Returns:
        df (pd.DataFrame): The modified DataFrame including the new columns with calculated forecast errors and excluding rows as per the exclusion criteria.
    """
    # Step 1: Calculate the average absolute forecast error for each analyst i forecast of firm j in year t
    df['afe_analyst_i'] = np.abs(df['estimated_eps'] - df['actual_eps'])
    
    df_grouped = df.groupby(['ibes_ticker_pk', 'analyst', 'fiscal_period_ending']).agg({'afe_analyst_i': 'mean'}).reset_index()
    df_grouped = df_grouped.rename(columns={'afe_analyst_i': 'afe_analyst_ijt_mean'})
    df = pd.merge(df, df_grouped, on=['ibes_ticker_pk', 'analyst', 'fiscal_period_ending'], how='left')
    
    # Step 2: Calculate the overall forecast error for each firm j in year t
    df['afe_firm_jt_mean'] = df.groupby(["ibes_ticker_pk", "fiscal_period_ending"])["afe_analyst_i"].transform("mean")
    
    # Step 3: Calculate the PMAFE for each analyst i forecast of firm j in year t
    df['pmafe'] = (df['afe_analyst_ijt_mean'] - df['afe_firm_jt_mean']) / df['afe_firm_jt_mean']
    # TODO Step 4: Exclude companies without a forecast
    df = df.dropna(subset=['pmafe'])

    return df


#### COLLAPSE DATA ####
def collapse_processed_df(df):
    """
    This function collapses/groups the input df into the final df so that one row should correspond to one analyst 
    i's forecast of firm j in fiscal year t with accuracy measure pmafe and other relevant features

    Collapses the input DataFrame to ensure each row uniquely represents an analyst 'i's final forecast for firm 'j' in fiscal year 't', focusing on mean estimated EPS and the forecast with the shortest horizon.

    The function performs two main operations:
    1. Calculates the mean estimated EPS for each analyst-firm-fiscal year combination, averaging all forecasts made by an analyst for a specific firm in a given year.
    2. Selects the forecast with the minimum forecast horizon for each analyst-firm-period as the analyst's final prediction, assuming the most immediate forecast before the earnings announcement represents the analyst's final stance.

    Parameters:
    - df (pd.DataFrame): A DataFrame with columns 'analyst', 'ibes_ticker_pk', 'fiscal_year', 'estimated_eps', and 'forecast_horizon', where each row is a specific forecast.

    Returns:
    - pd.DataFrame: Each row represents the analyst's final forecast for a firm in a fiscal year, including the mean EPS estimate and the forecast with the shortest horizon to the earnings announcement.

    """
    # mean of all estimates of an analyst i for a company j in a year t
    df['mean_estimate_ijt'] = df.groupby(['analyst','ibes_ticker_pk','fiscal_year'])['estimated_eps'].transform('mean')

    # summarison of all revisions of an analyst to a *mean* prediction/estimate row
    min_forecast = df.groupby(['ibes_ticker_pk', 'analyst', 'fiscal_period_ending'])['forecast_horizon'].idxmin()
    min_forecast_df = df.loc[min_forecast]

    return min_forecast_df



def analyst_experience(df):
    """
    Merges a DataFrame df with analyst experience from a parquet file, performing the merge on matching 'analyst' and year columns. 
    It transforms the 'experience' data into a new column 'general_analyst_experience_log'
    by applying a natural logarithm, treating zero values specially. 
    The original 'year' column is dropped, and 'experience' is renamed to 'general_analyst_experience'.

    Args:
        df (pandas.Dataframe): The DataFrame to be enhanced with analyst experience data.

    Returns:
        pandas.Dataframe: The enhanced DataFrame including the analyst's general experience 
        and its logarithmic transformation.
    """
    experience = pd.read_parquet('data/processed/analyst_experience.parquet')
    df = pd.merge(left=df, right=experience, how='left', left_on=['analyst','forecast_announce_year'], right_on=['analyst', 'year'])
    df.drop(columns=['year'], inplace=True)
    # calculate a log of a function
    df['general_analyst_experience_log'] = df['experience'].apply(lambda x: np.log(x) if x != 0 else 0)
    # rename column
    df = df.rename(columns={'experience': 'general_analyst_experience'})
    df = df.dropna(subset=['general_analyst_experience'])

    return df


def brokerage(df):
    """
    Function to add a dummy for each analyst that is employed by a brockerage that belongs to the 
    Top 10 % of brokerages by analyst count in year t
    Set to 1 if analyst i is employed by a firm in the top quantile during year t (fpedats_year), and set to 0 otherwise
    broker = df["estimator"]
    analyst = df["analyst"]
    analyst_count = Count of analysts per brokerage in year t
    Output: this function adds a new column to the dataframe called "top_10_brokerage" with the dummy variable
    """
    df['broker_size'] = df.groupby(['fiscal_year', 'estimator'])['analyst'].transform('nunique')
    top_10_thresholds = df.groupby('fiscal_year')['broker_size'].quantile(0.90).reset_index()  
    df['top_10'] = np.where(df['broker_size'] > df['fiscal_year'].map(top_10_thresholds.set_index('fiscal_year')['broker_size']), 1, 0)
    
    return df


def sic_codes(df):
    """
    Enhances the input DataFrame by merging it with a linking table containing SIC (Standard Industrial Classification) codes, based on matching ticker symbols.

    The function performs the following operations:
    1. Reads a linking table from a parquet file, which maps 'ticker' symbols to their corresponding SIC codes.
    2. Merges the input DataFrame with the linking table on 'ibes_ticker_pk' (in the input DataFrame) and 'ticker' (in the linking table), adding the SIC code to each matching row.
    3. Removes any rows that do not have a corresponding SIC code post-merge, ensuring that the resulting DataFrame only contains entries with valid industry classifications.

    Parameters:
    - df (pd.DataFrame): The input DataFrame, expected to contain a column 'ibes_ticker_pk' which holds the ticker symbols used for merging with the SIC codes.

    Returns:
    - pd.DataFrame: The enhanced DataFrame with an added 'sic' column for SIC codes. Rows without matching SIC codes are excluded from the result.

    Note:
    - The linking table is read from 'data/processed/linking_table.parquet', which must be present and correctly formatted with at least 'ticker' and 'sic' columns for the function to work.
    """

    linking_table = pd.read_parquet('data/processed/sic_linking_table.parquet')
    df = pd.merge(df, linking_table, how = 'left', left_on='ibes_ticker_pk', right_on='ticker')
    df = df.dropna(subset=['sic'])

    return df


def coverage(df):
    """
    Function to calculate the coverage of company j at the broker of analyst i. 
    As the count of the number of analysts following company j in year t at the same brokerage as analyst i

    Calculates various coverage metrics to analyze the extent and complexity of analyst coverage for companies within the dataset. This function adds several new columns to the input DataFrame, each representing a different dimension of coverage:

    1. 'broker_coverage': The number of analysts from the same brokerage as analyst 'i' that follow company 'j' in fiscal period 't'. This measures the internal coverage density of a company within a brokerage.
    2. 'analyst_portfolio_company_complexity_it': The number of unique companies followed by analyst 'i' in fiscal year 't', indicating the breadth of the analyst's coverage portfolio.
    3. 'analyst_following_jt': The total number of analysts following company 'j' in fiscal period 't', providing a measure of overall market attention to the company.
    4. 'analyst_portfolio_industry_complexity_it': The number of unique industries (based on SIC codes) followed by analyst 'i' in fiscal year 't', reflecting the diversity of the analyst's coverage across different sectors.

    Parameters:
    - df (pd.DataFrame): A pandas DataFrame expected to contain the columns 'ibes_ticker_pk', 'fiscal_period_ending', 'estimator' (brokerage identifier), 'analyst', 'fiscal_year', and 'sic' (Standard Industrial Classification code).

    Returns:
    - pd.DataFrame: The original DataFrame augmented with the new columns detailing coverage metrics.

    """
    df['broker_coverage'] = df.groupby(['ibes_ticker_pk','fiscal_period_ending', 'estimator'])['analyst'].transform('count')
    # Number of companies followed by analyst i in a year t
    df['analyst_portfolio_company_complexity_it'] = df.groupby(['analyst', 'fiscal_year'])['ibes_ticker_pk'].transform('nunique')
    # number of analysts following a company j in the year t
    df['analyst_following_jt'] = df.groupby(['ibes_ticker_pk','fiscal_period_ending'])['analyst'].transform('count')
    # number of industires followed by anlayst i in the year t
    df['analyst_portfolio_industry_complexity_it'] = df.groupby(['analyst', 'fiscal_year'])['sic'].transform('nunique')

    return df


def surprise(df):
    """
    Calculates the earnings surprise and its lag for each analyst's forecast in the DataFrame. The earnings surprise is 
    defined as the percentage difference between the actual earnings per share (EPS) and the analyst's mean estimate of the 
    EPS. The function also calculates the lag of the earnings surprise, which is the surprise value from the analyst's 
    previous forecast for the same company.

    Operations performed:
    - Calculates the earnings surprise as (actual EPS - mean estimated EPS) / mean estimated EPS.
    - Computes the lagged surprise value for each analyst-company pair, ensuring the first forecast for each pair has a 
      lagged surprise of 0.
    - Assigns a rank for each forecast by an analyst for a company based on the fiscal year, to facilitate the calculation 
      of the lagged surprise.
    - Removes rows where the surprise or its lag value is NaN, ensuring only complete records are retained.

    Parameters:
    - df (pd.DataFrame): Input DataFrame containing at least 'actual_eps', 'mean_estimate_ijt', 'analyst', 'ibes_ticker_pk', 
      and 'fiscal_year' columns.

    Returns:
    - pd.DataFrame: The modified DataFrame with two new columns added:
      - 'surprise': The earnings surprise for each forecast.
      - 'surprise_lag': The lagged earnings surprise, with the first forecast for each analyst-company pair set to 0, and 
        subsequent forecasts showing the previous year's surprise.
    """
    # mean estimate
    df['surprise'] = (df['actual_eps'] - df['mean_estimate_ijt']) / df['mean_estimate_ijt']
    df['surprise_lag'] = df.sort_values(by=['analyst', 'ibes_ticker_pk', 'fiscal_year']).groupby(['analyst', 'ibes_ticker_pk'])['surprise'].shift(1)
 
    # number of times analyst made a forecast for a company, starting with a 1 and adding +1 each year, e.g. 9th prediction = rank 9
    df['rank'] = df.groupby(['analyst', 'ibes_ticker_pk'])['fiscal_year'].rank(method="min")
    df.loc[df['rank'] == 1, 'surprise_lag'] = 0
    df.drop(columns=['rank'], inplace=True)
    
    # drop columns with zero
    df = df.dropna(subset = ['surprise'])
    df = df.dropna(subset = ['surprise_lag'])

    return df


#### DATA SCIENCE FUNCTIONS ####

df_forecast = load_datasets()
df_forecast = preprocessing_ibes(df_forecast)
df_forecast = calculate_pmafe(df_forecast)
df_forecast = collapse_processed_df(df_forecast)
df_forecast = analyst_experience(df_forecast)
df_forecast = brokerage(df_forecast)
df_forecast = sic_codes(df_forecast)
df_forecast = coverage(df_forecast)
df_forecast = surprise(df_forecast)

df_forecast.to_parquet('data/processed/ibes-forecasts_collapsed.parquet')