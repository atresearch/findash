from datetime import datetime
import pandas as pd
import QuantLib as ql


pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def py_to_ql_date(d):
    return ql.Date(d.day, d.month, d.year)

def ql_to_py_date(d):
    return datetime(d.year(), d.month(), d.dayOfMonth())

tenors = [1]

settings = [
    {
        'name': 'SimpleDayCounter, NullCalendar, Unadjusted',
        'day_count': ql.SimpleDayCounter(),
        'calendar': ql.NullCalendar(),
        'bussiness_convention': ql.Unadjusted
    },
    {
        'name': 'ActActISMA,GovernmentBond,Following',
        'day_count': ql.ActualActual(ql.ActualActual.ISMA),
        'calendar': ql.UnitedStates(ql.UnitedStates.GovernmentBond),
        'bussiness_convention': ql.Following
    },
    {
        'name': 'Actual360,GovernmentBond,Following',
        'day_count': ql.Actual360(),
        'calendar': ql.UnitedStates(ql.UnitedStates.GovernmentBond),
        'bussiness_convention': ql.Following
    },
]

settlement_days = 0
end_of_month = False 
face_amount = 100
coupon_frequency = ql.Period(ql.Semiannual)
        
for setting in settings:
    day_count = setting['day_count']
    calendar = setting['calendar']
    bussiness_convention = setting['bussiness_convention']
    
    dates = pd.date_range('2022-12-20', periods=60)
    df = pd.DataFrame(index=dates)
    df.index.name = 'CalcDate'

    for m in tenors:
        ql_dates = []
        ql_days = []
        ql_years = []
        
        ql_bond_dates = []
        ql_bond_days = []
        ql_bond_years = []
        
        ql_bond_npvs = []
        
        for d in dates:
            calc_date = py_to_ql_date(d)
            ql.Settings.instance().evaluationDate = calc_date

            # --------------------------------------------------------
            # Date offset, x months forwards
            # --------------------------------------------------------

            termination_date = calc_date + ql.Period(m, ql.Months)
            ql_day = termination_date - calc_date
            ql_year = day_count.yearFraction(calc_date, termination_date)

            ql_dates.append(ql_to_py_date(termination_date))
            ql_days.append(ql_day)
            ql_years.append(ql_year)
            
            # --------------------------------------------------------
            # Schedule of a bond
            # --------------------------------------------------------            
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
            
            bond_date = list(schedule)[-1]
            
            ql_bond_dates.append(ql_to_py_date(bond_date))
            ql_bond_days.append(bond_date - calc_date)
            ql_bond_years.append(day_count.yearFraction(calc_date, bond_date))      
            
            # --------------------------------------------------------    
            # Zero curve
            # --------------------------------------------------------         
            spot_dates = [calc_date, calc_date + ql.Period(m+1, ql.Months)]
            spot_rates = [0.04, 0.04]
            
            interpolation = ql.Linear()
            compounding = ql.Compounded
            compounding_frequency = ql.Annual
            spot_curve = ql.ZeroCurve(spot_dates, spot_rates, day_count, calendar,
                           interpolation, compounding, compounding_frequency)
            
            spot_curve_handle = ql.YieldTermStructureHandle(spot_curve)

            # --------------------------------------------------------  
            # Bond price
            # --------------------------------------------------------    
            bond = ql.ZeroCouponBond(
                settlement_days,
                calendar,
                face_amount,
                termination_date,
                bussiness_convention,
                face_amount,
                calc_date # issue date
            )

            # Set Valuation engine
            bond_engine = ql.DiscountingBondEngine(spot_curve_handle)
            bond.setPricingEngine(bond_engine)

            # Calculate present value
            value = bond.NPV()
            ql_bond_npvs.append(value)
            
        df[f'+{m}M'] = ql_dates
        df[f'+{m}M-days'] = ql_days
        df[f'+{m}M-yr'] = ql_years
        
        df[f'+{m}B'] = ql_bond_dates
        df[f'+{m}B-days'] = ql_bond_days
        df[f'+{m}B-yr'] = ql_bond_years
        df[f'{m}-npv'] = ql_bond_npvs
    print()
    print(setting['name'])
    print(df)