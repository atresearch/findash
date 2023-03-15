import pandas as pd

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


def load_rates(path):
    df = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
    return df
