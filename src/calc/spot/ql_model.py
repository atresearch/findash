from calc.spot.base import BaseSpotCurveModel
import QuantLib as ql
from datetime import datetime

debug = False


def make_ql_date(calc_date_str):
    d = datetime.strptime(calc_date_str, '%Y-%m-%d')
    return ql.Date(d.day, d.month, d.year)


class QLModel(BaseSpotCurveModel):
    def __init__(self, calc_date_str, simplified=True):
        self.yieldcurve = None
        self.calc_date = make_ql_date(calc_date_str)
        self.simplified = simplified

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
        if self.simplified:
            calendar = ql.NullCalendar()
            day_count = ql.SimpleDayCounter()
            bussiness_convention = ql.Unadjusted
        else:
            calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
            day_count = ql.ActualActual(ql.ActualActual.ISMA)
            bussiness_convention = ql.Following

        settlement_days = 0
        end_of_month = False 
        face_amount = 100
        coupon_frequency = ql.Period(ql.Semiannual)

        # create helpers from fixed rate bonds
        helpers = []
        for m, r in zip(tenors, par_rates):
            m = int(m)
            termination_date = self.calc_date + ql.Period(m, ql.Months)

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
            schedule_dates = list(schedule)
            if debug:
                print(f'\nBond with tenor {m} months has {len(schedule_dates)} coupons.')
                print(schedule_dates)
                print([d - self.calc_date for d in schedule_dates])

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
        # self.yieldcurve = ql.PiecewiseLogLinearDiscount(self.calc_date, helpers, day_count)
        # yieldcurve = ql.PiecewiseLogCubicDiscount(calc_date, helpers, day_count)
        # yieldcurve = ql.PiecewiseLinearZero(calc_date, helpers, day_count)
        self.yieldcurve = ql.PiecewiseCubicZero(self.calc_date, helpers, day_count)

    def spot_rates(self, tenors):
        spots = []
        for m in tenors:
            zero_rate = self.yieldcurve.zeroRate(int(m)/12, ql.Compounded, ql.Semiannual).rate()
            spots.append(zero_rate)
        return spots
