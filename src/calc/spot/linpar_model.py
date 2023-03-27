import numpy as np
from calc.spot.base import BaseSpotCurveModel


class LinearParCurveModel(BaseSpotCurveModel):
    def __init__(self):
        self.spot = None
        pass
    
    def init_param(self, tenors, par_rates):
        pass
                
    def get_params(self):
        return None
    
    def set_params(self, params):
        pass
    
    def fit(self, tenors, par_rates):
        pars = np.interp(np.arange(361), tenors, par_rates) 
        df = np.zeros_like(pars)
        df[0] = 1.0
        
        for tenor in range(1, 361):
            coupon_cashflow = 0.5 * pars[tenor]
            accrued_time = (6-tenor) % 6
            accrued_interest = coupon_cashflow * accrued_time / 6
            df_sum = np.sum(df[np.arange(tenor-6, 0, -6)])
            df[tenor] = (1 + accrued_interest - df_sum * coupon_cashflow) / (1 +coupon_cashflow)

        t = np.arange(361) / 12
        t[0] = 1 
        self.spot = -np.log(df) / t
        self.spot[0] = self.spot[1]
    
    def spot_rates(self, tenors):
        return self.spot[tenors]
