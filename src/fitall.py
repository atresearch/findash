import pandas as pd
import numpy as np
import QuantLib as ql

# -------------------------------------------------------------------------
# Quantlib Settings
# -------------------------------------------------------------------------
calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
day_count = ql.ActualActual(ql.ActualActual.ISMA)
bussiness_convention = ql.Following
settlement_days = 0
end_of_month = False
face_amount = 100
coupon_frequency = ql.Period(ql.Semiannual)

# Read the par-rates file
df = pd.read_csv('rates.csv', parse_dates=["Date"]).set_index("Date")
print(df)

# -------------------------------------------------------------------------
# Convert column header string (like "3 Yr") into number of months (36)
# -------------------------------------------------------------------------
period_code_months = {'Mo': 1, 'Yr': 12}

def tenor_str_to_num_months(str):
    num, period_code = str.split()
    return int(num) * period_code_months[period_code]

# a list of tenors in months       
num_months = [tenor_str_to_num_months(s) for s in df.columns]
print('num_months =', num_months)


# -------------------------------------------------------------------------
# Loop over all rows in the rates.csvfile
# -------------------------------------------------------------------------
results = []
print('\nmain loop')
for date, quotes in df.iterrows():

    print('date =', date, quotes.values)

    # Parse the date and tell QL that this is the calculation date
    calc_date = ql.Date(date.day, date.month, date.year)
    ql.Settings.instance().evaluationDate = calc_date

    # Create a list of bond=helpers for each quote
    helpers = []

    # Loop over all quotes on this date
    for m, par_rate in zip(num_months, 0.01*quotes.values):

        # Skip NaN / missing quotes
        if np.isnan(par_rate):
            continue

        # print(f'num_months = {m}, par_rate = {par_rate:4f}')

        # The bond maturity date
        termination_date = calc_date + ql.Period(m, ql.Months)

        # Coupon schedule
        schedule = ql.Schedule(
            calc_date,
            termination_date,
            coupon_frequency,
            calendar,
            bussiness_convention,
            bussiness_convention,
            ql.DateGeneration.Backward,
            end_of_month
        )

        # Fixed rate bond
        helper = ql.FixedRateBondHelper(
            ql.QuoteHandle(ql.SimpleQuote(face_amount)),
            settlement_days,
            face_amount,
            schedule,
            [par_rate],
            day_count,
            bussiness_convention,
        )

        helpers.append(helper)
    
    # Skip the curve if there were not valid quotes
    if len(helpers) == 0:
        continue

    # Fit
    yieldcurve = ql.PiecewiseCubicZero(calc_date, helpers, day_count)    
    yieldcurve.enableExtrapolation()

    # Lookup values on the curve
    spots = []
    for m in num_months:
        yrs = m / 12
        try:
            zero_rate = yieldcurve.zeroRate(yrs, ql.Compounded, ql.Semiannual).rate()
        except RuntimeError:
            print(f'skipped m={m}')
            continue

        spots.append(round(zero_rate * 100, 4))
        # sprint(f'm = {m}, spot = {zero_rate}')

    spot_curve = dict(zip(df.columns, spots))
    spot_curve['Date'] = date
    results.append(spot_curve)
    
ans = pd.DataFrame(results).set_index("Date")
print(ans)
ans.to_csv('spots.csv')