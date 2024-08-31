import schwabdev
import os
import dotenv
import requests
import base64
import time
import client
import json
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import pyodbc
import lxml
from pandas import json_normalize

# Load environment variables.
dotenv.load_dotenv()

# Set up connection to MySQL database with environment variables.
server_name = os.getenv("servername")
database_name = os.getenv("database")

# Creating the connection string
connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server_name};Database={database_name};Trusted_Connection=yes;"

# Connecting to SQL Server
conn = pyodbc.connect(connection_string)

# Create a cursor object to execute SQL query.
cursor = conn.cursor()

# Setting table names to be used later.
market_table_name = 'market_data'
tickers_table_name = 'tickers_data'
fundamentals_table_name = 'fundamentals_data_table'

# Connecting to the Schwab API using environment variables.
client = schwabdev.Client(os.getenv("app_key"), os.getenv("app_secret"))
client.update_tokens_auto()

# Scraping data from wikipedia to always have an updated list of the S&P500
sp500link = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#S&P_500_component_stocks"
tickers = pd.read_html(sp500link, header=0)[0]
tickers.to_csv(r"C:\Users\garri\OneDrive\Desktop\Personal Projects\SchwabAPI\sp500list.csv", index=False)
# Making the Symbol column into a list to later iterate through.
trackers = tickers['Symbol'].tolist()
print("S&P500 data scraped.")

# Setting empty list to hold each dataframe.
market_data_df = []
fund = client.instruments("MSFT", 'fundamental').json()
fundamental_data = fund['instruments'][0]['fundamental']
columns = list(fundamental_data.keys())
fund_data_df = pd.DataFrame(columns=columns)


# Looping through the trackers in the list.
for tracker in trackers: 
    try:
        # Remove periods from the symbol name
        clean_tracker = tracker.replace('.', '')
        # Using the Schwab API Price_History method to get candle values every minute.
        data = client.price_history(f"{clean_tracker}", "year", 5, "daily").json()
        # Normalizing the json file into a dataframe.
        market_df = pd.json_normalize(data['candles'])
        # Converting Datetime column into a DateTime datatype.
        market_df['datetime'] = pd.to_datetime(market_df['datetime'], unit= 'ms')
        # Setting the Symbol column for each row to the tracker value ('AAPL', 'MFST', etc.)
        market_df['Symbol']= clean_tracker
        # Appending each dataframe to the list.
        market_data_df.append(market_df)
        
        fund = client.instruments(f"{clean_tracker}", 'fundamental').json()
        # Access the nested dictionary
        fundamental_data = fund['instruments'][0]['fundamental']
        # Replace None values with blank
        fundamental_values = {key: (value if value is not None else '') for key, value in fundamental_data.items()}
        # Align the columns with the existing DataFrame
        aligned_values = {col: fundamental_values.get(col, '') for col in columns}
        # Create a DataFrame with the aligned values
        temp_df = pd.DataFrame([aligned_values])
        # Append the new row to the fund_data_df
        fund_data_df = pd.concat([fund_data_df, temp_df], ignore_index=True)
        
        print(f"Data for {clean_tracker} downloaded successfully.")
    except Exception as e:
        print(f"Failed to download data for {clean_tracker}: {e}")

# Concatenating each dataframe to one master market data df.
market_data = pd.concat(market_data_df, ignore_index= True)

# Renaming columns.
market_data = market_data.rename(columns={"open": 'Open', "high": 'High', "low": 'Low', "close": 'Close', "volume": 'Volume', "datetime": 'Date'})

# Reordering columns.
market_data = market_data.reindex(columns=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'])

# Creating CSV of master data and fundamentals data.
market_data.to_csv(r"C:\Users\garri\OneDrive\Desktop\Personal Projects\SchwabAPI\market_data_test.csv", index= False, date_format='%Y-%m-%d %H:%M:%S')

fund_data_df.to_csv(r"C:\Users\garri\OneDrive\Desktop\Personal Projects\SchwabAPI\fundamentals_data.csv", index= False)

print("Files created in directory.")

# SQL commands to drop and recreate tables
drop_and_create_market_data = f"""
IF OBJECT_ID('{market_table_name}', 'U') IS NOT NULL
    DROP TABLE {market_table_name};

CREATE TABLE {market_table_name} (
    [Date] DATETIME,
    [Symbol] NVARCHAR(10),
    [Open] FLOAT,
    [High] FLOAT,
    [Low] FLOAT,
    [Close] FLOAT,
    [Volume] FLOAT
);
"""

drop_and_create_tickers_data = f"""
IF OBJECT_ID('{tickers_table_name}', 'U') IS NOT NULL
    DROP TABLE {tickers_table_name};

CREATE TABLE {tickers_table_name} (
    [Symbol] NVARCHAR(10),
    [Security] NVARCHAR(255),
    [GICS Sector] NVARCHAR(255),
    [GICS Sub-Industry] NVARCHAR(255),
    [Headquarters Location] NVARCHAR(255),
    [Date added] DATETIME,
    [CIK] NVARCHAR(10),
    [Founded] NVARCHAR(255)
);
"""

drop_and_create_fundamentals_data = f"""
IF OBJECT_ID('{fundamentals_table_name}', 'U') IS NOT NULL
    DROP TABLE {fundamentals_table_name};

CREATE TABLE {fundamentals_table_name} (
    [symbol] NVARCHAR(10),
    [high52] FLOAT,
    [low52] FLOAT,
    [dividendAmount] FLOAT,
    [dividendYield] FLOAT,
    [dividendDate] DATETIME,
    [peRatio] FLOAT,
    [pegRatio] FLOAT,
    [pbRatio] FLOAT,
    [prRatio] FLOAT,
    [pcfRatio] FLOAT,
    [grossMarginTTM] FLOAT,
    [grossMarginMRQ] FLOAT,
    [netProfitMarginTTM] FLOAT,
    [netProfitMarginMRQ] FLOAT,
    [operatingMarginTTM] FLOAT,
    [operatingMarginMRQ] FLOAT,
    [returnOnEquity] FLOAT,
    [returnOnAssets] FLOAT,
    [returnOnInvestment] FLOAT,
    [quickRatio] FLOAT,
    [currentRatio] FLOAT,
    [interestCoverage] FLOAT,
    [totalDebtToCapital] FLOAT,
    [ltDebtToEquity] FLOAT,
    [totalDebtToEquity] FLOAT,
    [epsTTM] FLOAT,
    [epsChangePercentTTM] FLOAT,
    [epsChangeYear] FLOAT,
    [epsChange] FLOAT,
    [revChangeYear] FLOAT,
    [revChangeTTM] FLOAT,
    [revChangeIn] FLOAT,
    [sharesOutstanding] FLOAT,
    [marketCapFloat] FLOAT,
    [marketCap] FLOAT,
    [bookValuePerShare] FLOAT,
    [shortIntToFloat] FLOAT,
    [shortIntDayToCover] FLOAT,
    [divGrowthRate3Year] FLOAT,
    [dividendPayAmount] FLOAT,
    [dividendPayDate] DATETIME,
    [beta] FLOAT,
    [vol1DayAvg] FLOAT,
    [vol10DayAvg] FLOAT,
    [vol3MonthAvg] FLOAT,
    [avg10DaysVolume] FLOAT,
    [avg1DayVolume] FLOAT,
    [avg3MonthVolume] FLOAT,
    [declarationDate] DATETIME,
    [dividendFreq] FLOAT,
    [eps] FLOAT,
    [dtnVolume] FLOAT,
    [nextDividendPayDate] DATETIME,
    [nextDividendDate] DATETIME,
    [fundLeverageFactor] FLOAT
);
"""

# Execute the SQL commands to drop and recreate tables
cursor.execute(drop_and_create_market_data)
cursor.execute(drop_and_create_tickers_data)
cursor.execute(drop_and_create_fundamentals_data)
conn.commit()

print("SQL Server Tables created.")

# Iterate through each df and insert them into the database
try:

    # Insert market data
    for _, row in market_data.iterrows():
        query = f"INSERT INTO {market_table_name} ([Date], [Symbol], [Open], [High], [Low], [Close], [Volume]) VALUES (?, ?, ?, ?, ?, ?, ?)"
        values = (row['Date'], row['Symbol'], row['Open'], row['High'], row['Low'], row['Close'], row['Volume'])
        cursor.execute(query, values)
    
    # Insert ticker data
    for _, row in tickers.iterrows():
        query = f"INSERT INTO {tickers_table_name} ([Symbol], [Security], [GICS Sector], [GICS Sub-Industry], [Headquarters Location], [Date added], [CIK], [Founded]) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        values = (row['Symbol'], row['Security'], row['GICS Sector'], row['GICS Sub-Industry'], row['Headquarters Location'], row['Date added'], row['CIK'], row['Founded'])
        cursor.execute(query, values)
    
    # Insert fundamentals data
    for _, row in fund_data_df.iterrows():
        query = f"""
        INSERT INTO {fundamentals_table_name} ([symbol], [high52], [low52], [dividendAmount], [dividendYield], [dividendDate],
        [peRatio], [pegRatio], [pbRatio], [prRatio], [pcfRatio], [grossMarginTTM], [grossMarginMRQ], [netProfitMarginTTM],
        [netProfitMarginMRQ], [operatingMarginTTM], [operatingMarginMRQ], [returnOnEquity], [returnOnAssets], [returnOnInvestment],
        [quickRatio], [currentRatio], [interestCoverage], [totalDebtToCapital], [ltDebtToEquity], [totalDebtToEquity], [epsTTM],
        [epsChangePercentTTM], [epsChangeYear], [epsChange], [revChangeYear], [revChangeTTM], [revChangeIn], [sharesOutstanding],
        [marketCapFloat], [marketCap], [bookValuePerShare], [shortIntToFloat], [shortIntDayToCover], [divGrowthRate3Year],
        [dividendPayAmount], [dividendPayDate], [beta], [vol1DayAvg], [vol10DayAvg], [vol3MonthAvg], [avg10DaysVolume],
        [avg1DayVolume], [avg3MonthVolume], [declarationDate], [dividendFreq], [eps], [dtnVolume], [nextDividendPayDate],
        [nextDividendDate], [fundLeverageFactor]) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        values = (
            row['symbol'], row['high52'], row['low52'], row['dividendAmount'], row['dividendYield'], row['dividendDate'],
            row['peRatio'], row['pegRatio'], row['pbRatio'], row['prRatio'], row['pcfRatio'], row['grossMarginTTM'],
            row['grossMarginMRQ'], row['netProfitMarginTTM'], row['netProfitMarginMRQ'], row['operatingMarginTTM'],
            row['operatingMarginMRQ'], row['returnOnEquity'], row['returnOnAssets'], row['returnOnInvestment'], row['quickRatio'],
            row['currentRatio'], row['interestCoverage'], row['totalDebtToCapital'], row['ltDebtToEquity'], row['totalDebtToEquity'],
            row['epsTTM'], row['epsChangePercentTTM'], row['epsChangeYear'], row['epsChange'], row['revChangeYear'], row['revChangeTTM'],
            row['revChangeIn'], row['sharesOutstanding'], row['marketCapFloat'], row['marketCap'], row['bookValuePerShare'],
            row['shortIntToFloat'], row['shortIntDayToCover'], row['divGrowthRate3Year'], row['dividendPayAmount'],
            row['dividendPayDate'], row['beta'], row['vol1DayAvg'], row['vol10DayAvg'], row['vol3MonthAvg'], row['avg10DaysVolume'],
            row['avg1DayVolume'], row['avg3MonthVolume'], row['declarationDate'], row['dividendFreq'], row['eps'], row['dtnVolume'],
            row['nextDividendPayDate'], row['nextDividendDate'], row['fundLeverageFactor']
        )
        cursor.execute(query, values)

    # Commit the transaction
    conn.commit()

except Exception as e:
    conn.rollback()
    print(f"An error occurred: {e}")
finally:
    cursor.close()
    conn.close()
    print("SQL Server tables populated.")
