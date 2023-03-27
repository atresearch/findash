import QuantLib as ql
from datetime import datetime

def make_ql_date(calc_date_str):
    d = datetime.strptime(calc_date_str, '%Y-%m-%d')
    return ql.Date(d.day, d.month, d.year) 
    
def par_curve_to_spot(calc_date_str, maturity_months, par_rates, new_maturity_months=None):
    """Convert a list op par-rates & tenors into spot-rates, potentially sampled at different tenors.

    Args:
        calc_date_str (string 'yyyy-mm-dd'): The current date or calculation date.
        maturity_months (list[int]): A list of tenors defined in nr of months, e.g.[1,2,3,6,12,24,...]
        par_rates (list[float]): A list of par-rates. e.g. [1,2,3] means par-rates of 1%,2%, 3%.
        new_maturity_months (list[int], optional): A list of new tenors for the output spot curve. Defaults to None.

    Returns:
        tenors, spot-rates: _description_
    """

    if not new_maturity_months:
        new_maturity_months = maturity_months

    # Parse the calc_date string and convert it to a Quantlib Date type.
    calc_date = make_ql_date(calc_date_str)

    # Initilaize ql
    ql.Settings.instance().evaluationDate = calc_date

    # Conventions
    calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
    bussiness_convention = ql.Unadjusted
    day_count = ql.ActualActual(ql.ActualActual.Bond)
    end_of_month = False
    settlement_days = 0
    face_amount = 100
    coupon_frequency = ql.Period(ql.Semiannual)
    settlement_days = 0

    # create helpers from fixed rate bonds
    helpers = []
    for m, r in zip(maturity_months, par_rates):
        
        termination_date = calc_date + ql.Period(m, ql.Months)
        
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

        helper = ql.FixedRateBondHelper(
            ql.QuoteHandle(ql.SimpleQuote(face_amount)),
            settlement_days,
            face_amount,
            schedule,
            [r/100.0],
            day_count,
            bussiness_convention,
        )

        helpers.append(helper)

    # Define the yield curve    
    #yieldcurve = ql.PiecewiseLogLinearDiscount(calc_date, helpers, day_count)
    #yieldcurve = ql.PiecewiseLogCubicDiscount(calc_date, helpers, day_count)
    #yieldcurve = ql.PiecewiseLinearZero(calc_date, helpers, day_count)
    yieldcurve = ql.PiecewiseCubicZero(calc_date, helpers, day_count)
    #yieldcurve = ql.PiecewiseLinearForward(calc_date, helpers, day_count)
    #yieldcurve = ql.PiecewiseSplineCubicDiscount(calc_date, helpers, day_count)


    # get spot rates
    spots = []
    tenors_in_years = []
    for m in new_maturity_months:   
        yrs = m/12
        d = calc_date + ql.Period(m, ql.Months)
        zero_rate = yieldcurve.zeroRate(yrs, ql.Compounded, ql.Semiannual)
        tenors_in_years.append(yrs)
        eq_rate = zero_rate.equivalentRate(day_count, ql.Compounded, ql.Semiannual, calc_date, d).rate()
        spots.append(100*eq_rate)

    return tenors_in_years, spots
