from abc import ABC, abstractmethod
import numpy as np
from scipy.optimize import minimize

debug = False

class BaseSpotCurveModel(ABC):

    @abstractmethod
    def init_param(self, tenors, par_rates):
        pass

    @abstractmethod
    def get_params(self):
        pass

    @abstractmethod
    def set_params(self, params):
        pass

    @abstractmethod
    def spot_rates(self, tenors):
        pass

    def fit_error(self, params, tenors, par_rates):
        self.set_params(params)
        bond_prices = [self.bond_price(tenor, coupon) for tenor, coupon in zip(tenors, par_rates)]
        price_err = 100 * np.asarray(bond_prices) - 100
        rmse = np.mean(price_err**2)**0.5
        return rmse

    def fit(self, tenors, par_rates):
        self.init_param(tenors, par_rates)
        ans = minimize(
            self.fit_error, 
            self.get_params(),
            (tenors, par_rates),
            tol=1E-6,
            method='BFGS',
            options={'disp': debug}
        )
        self.set_params(ans.x)
        if debug:
            print(
                [self.bond_price(tenor, coupon) for tenor, coupon in zip(tenors, par_rates)]
            )

    def discount_factors(self, tenors):
        return np.exp(-self.spot_rates(tenors) * tenors/12.0)

    def forward_rates(self, tenors):
        r = self.spot_rates(tenors)
        rt = r * tenors
        ans = np.diff(rt) / np.diff(tenors)
        return np.insert(ans, 0, r[0])

    def bond_price(self, tenor, coupon):
        if tenor < 6:
            bond_price = (1 + coupon * tenor / 12.0) * self.discount_factors(tenor)
            return bond_price

        cashflow_times = np.arange(tenor, 0, -6)[::-1]

        # the size of the cashflows
        cashflow_amounts = 0.5 * coupon * np.ones_like(cashflow_times)
        cashflow_amounts[-1] += 1  # add terminal payment

        # the npv of these cashflows using the spot curve
        cashflow_discount_factors = self.discount_factors(cashflow_times)

        # clean price (without accruel)
        bond_dirty_price = np.sum(cashflow_amounts * cashflow_discount_factors)
        return bond_dirty_price
        
        # Accruel
        time_since_last_coupon = (6 - tenor) % 6
        accruel = (time_since_last_coupon / 6) * (coupon / 2)
        bond_clean_price = bond_dirty_price - accruel
        return bond_clean_price
