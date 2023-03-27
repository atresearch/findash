import numpy as np
from calc.spot.base import BaseSpotCurveModel
from scipy import interpolate  


class CubicSplineSpotCurveModel(BaseSpotCurveModel):
    def __init__(self, bc_type=('natural', 'natural')):
        self.bc_type = bc_type
        self.model = None
        self.x = None
        self.y = None
    
    def init_param(self, tenors, par_rates):
        self.x = tenors.copy()
        self.y = 2 * np.log(1 + par_rates / 2)
        self.set_params(self.get_params())

    def get_params(self):
        return self.y
    
    def set_params(self, params):
        self.y = params
        self.model = interpolate.CubicSpline(self.x, self.y, bc_type=self.bc_type)

    def spot_rates(self, tenors):
        return self.model(tenors)