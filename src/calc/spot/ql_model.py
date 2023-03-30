from calc.spot.base import BaseSpotCurveModel
import QuantLib as ql
from datetime import datetime


def make_ql_date(calc_date_str):
    d = datetime.strptime(calc_date_str, '%Y-%m-%d')
    return ql.Date(d.day, d.month, d.year)


class QLModel(BaseSpotCurveModel):
    def __init__(self, calc_date_str, simple_months=True):
        self.simple_months = simple_months
        self.yieldcurve = None
        self.calc_date = make_ql_date(calc_date_str)

    def init_param(self, tenors, par_rates):
        pass

    def get_params(self):
        return None

    def set_params(self, params):
        pass

    def fit(self, tenors, par_rates):

        # Initilaize ql
        ql.Settings.instance().evaluationDate = self.calc_date

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
        for m, r in zip(tenors, par_rates):
            m = int(m)
            print(m, type(m))
            print(ql.Months)
            print(self.calc_date)
            print(ql.Period(m, ql.Months))

            termination_date = self.calc_date + ql.Period(m, ql.Months)
            print(termination_date)
            schedule = ql.Schedule(
                self.calc_date,
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
                [r],
                day_count,
                bussiness_convention,
            )

            helpers.append(helper)

        # Define the yield curve
        # yieldcurve = ql.PiecewiseLogLinearDiscount(calc_date, helpers, day_count)
        # yieldcurve = ql.PiecewiseLogCubicDiscount(calc_date, helpers, day_count)
        # yieldcurve = ql.PiecewiseLinearZero(calc_date, helpers, day_count)
        self.yieldcurve = ql.PiecewiseCubicZero(self.calc_date, helpers, day_count)

    def spot_rates(self, tenors):
        # get spot rates
        day_count = ql.ActualActual(ql.ActualActual.Bond)
        spots = []
        for m in tenors:
            m = int(m)
            yrs = m/12
            d = self.calc_date + ql.Period(m, ql.Months)
            zero_rate = self.yieldcurve.zeroRate(yrs, ql.Compounded, ql.Semiannual)
            eq_rate = zero_rate.equivalentRate(day_count, ql.Compounded, ql.Semiannual, self.calc_date, d).rate()
            spots.append(eq_rate)

        return spots
