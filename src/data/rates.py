import pandas as pd
from data.storage_backend import TextStreamProvider

# A helper dictionafry for looking up the 'period sizes'
period_years = {
    'Mo': 1/12,
    'Yr': 1
}

def tenor_name_to_year(tenor_name):
    """Convert a string like "5 Mo" to number of years like 5/12 """

    num, period = tenor_name.split(' ')
    year = int(num) * period_years[period]
    return year


def load_rates(stream: TextStreamProvider) -> pd.DataFrame:
    df = pd.read_csv(stream, parse_dates=["Date"]).set_index("Date")
    return df


def missing_dates(df):
    return pd.date_range(
        start=df.index[0], 
        end=df.index[-1]
        ).difference(df.index).strftime("%Y-%m-%d").to_list()
