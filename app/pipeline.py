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

    # file_path_ibes = "../data/raw/ibes-forecasts.zip"
    # data/raw/ibes-forecasts.parquet
    df_forecasts = pd.read_parquet('data/raw/ibes-forecasts.parquet')
    link_to_crisp = pd.read_parquet('data/raw/crisp-computsat-link.parquet')
    # TODO join tables?? or perform it later

    return df_forecasts


### Service functions
def convert_to_datetime(df):
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
        4.2 Exclude forecasts for companies which only one analyst provides a forecast #TODO double check if we need to compute nr of forecasts
        4.3 Exclude all analysts appearing in the initial 2-3 years of the dataset #TODO will replaced with the analyst experience

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
    
    # #3 change format
    df = convert_to_datetime(df)

    # #4 Filter columns
    # 4.1 Include only forecasts issued no earlier than 1 year ahead and no later than 30 days before fiscal year end
    df['difference_date'] = df['fpedats'] - df['anndats']
    df = df[(df['difference_date']> pd.Timedelta(days=30))&(df['difference_date']<pd.Timedelta(days=365))]

    # 4.2 
    # TODO

    # #5 Rename columns
    df = df.rename(columns={"ticker": "ibes_ticker_pk", "oftic": "official_ticker", "analys": "analyst", 
                                "value": "estimated_eps", "fpedats": "fiscal_period_ending", 
                                "revdats": "revision_date", "anndats": "announce_date", 
                                "actual": "actual_eps", "anndats_act": "announce_date_actual",
                                "difference_date": "forecast_horizon"})

    # #6 Joins
    # 6.1 Analyst experience 
    # load data
    df['announce_year'] = df.announce_date.dt.year
    df['fpedats_year'] = df.fiscal_period_ending.dt.year

    experience = pd.read_parquet('data/processed/analyst_experience.parquet')
    df = pd.merge(left=df, right=experience, how='left', left_on=['analyst','announce_year'], right_on=['analyst', 'year'])
    df.drop(columns=[ 'year'], inplace=True)

    return df


# TODO not sure if needed anymore
def preprocessing_compustat(df):
    # reduce to highest level of SIC code
    df.loc[df['sic'].isna(), 'sic'] = -1 
    df['sic'] = df['sic'].astype(str).str[:2]
    df['sic'] = df['sic'].astype('int')
    
    
#### ADD DV AND FEATURE FUNCTIONS ####

def calculate_pmafe(df:pd.DataFrame) -> pd.DataFrame:
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
    This function collapses/groups the input df into the final df so that one row should correspond to one analyst 
    i's forecast of firm j in fiscal year t with accuracy measure pmafe and other relevant features
    """
    min_forecast = df.groupby(['ibes_ticker_pk', 'analyst', 'fiscal_period_ending'])['forecast_horizon'].idxmin()
    min_forecast_df = df.loc[min_forecast]
    min_forecast_df['analyst_following_j'] = min_forecast_df.groupby(['ibes_ticker_pk','fiscal_period_ending'])['analyst'].transform('count')
    return min_forecast_df




def top_10_brokerage(df):
    """
    Function to add a dummy for each analyst that is employed by a brockerage that belongs to the 
    Top 10 % of brokerages by analyst count in year t
    Set to 1 if analyst i is employed by a firm in the top quantile during year t (fpedats_year), and set to 0 otherwise
    broker = df["estimator"]
    analyst = df["analyst"]
    analyst_count = Count of analysts per brokerage in year t
    Output: this function adds a new column to the dataframe called "top_10_brokerage" with the dummy variable
    """
    # setup
    df["top_10_brokerage"] = 0
    # get top 10 % of brokerages by analyst count per year
    top_10 = df.groupby('fpedats_year')['analyst_following_j'].quantile(0.9)
    # loop through each year
    # TODO if a year will be needed for experience as well, mb replace
    for year in df['fpedats_year'].unique():
        # get the top 10 % of brokerages by analyst count for the year
        top_10_brokerages = df[df['fpedats_year'] == year][df['analyst_following_j'] >= top_10[year]]['estimator']
        # set the dummy to 1 if the brokerage is in the top 10 % of brokerages by analyst count
        df.loc[df['estimator'].isin(top_10_brokerages.index), 'top_10_brokerage'] = 1    
    
    return df


#### DATA SCIENCE FUNCTIONS ####



df_forecast = load_datasets()
df_forecast = preprocessing_ibes(df_forecast)
df_forecast = calculate_pmafe(df_forecast)
df_forecast = collapse_processed_df(df_forecast)

df_forecast = top_10_brokerage(df_forecast)
print(df_forecast.head(10))
# data/raw/ibes-forecasts.parquet
# data= pd.read_parquet('data/raw/ibes-forecasts.parquet')
# print(data.head(10))