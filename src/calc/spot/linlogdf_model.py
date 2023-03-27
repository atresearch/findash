import numpy as np
from calc.spot.base import BaseSpotCurveModel


class LinearLogDFSpotCurveModel(BaseSpotCurveModel):
    def __init__(self):
        self.x = None
        self.y = None
    
    def init_param(self, tenors, par_rates):
        self.x = tenors.copy()
        self.y = par_rates * tenors
        self.set_params(self.get_params())

    def get_params(self):
        return self.y
    
    def set_params(self, params):
        self.y = params

    def spot_rates(self, tenors):
        return np.interp(tenors, self.x, self.y) / tenors