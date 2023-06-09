import numpy as np
from calc.spot.base import BaseSpotCurveModel
from calc.util import cont_to_biannual
from scipy import interpolate  


class MonoCubicSplineSpotCurveModel(BaseSpotCurveModel):
    def __init__(self, bc_type=('natural', 'natural')):
        self.bc_type = bc_type
        self.model = None
        self.x = None
        self.y = None
    
    def init_param(self, tenors, par_rates):
        self.x = tenors.copy()
        self.y = 2 * np.log(1 + par_rates / 2)
        self.y[tenors < 6] = (12*np.log(1 + par_rates*tenors/12) / tenors)[tenors < 6]
        self.set_params(self.get_params())

    def get_params(self):
        return self.y
    
    def set_params(self, params):
        self.y = params
        self.model = interpolate.PchipInterpolator(
            self.x,
            self.y,
            extrapolate=True
        )

    def spot_rates(self, tenors):
        return self.model(tenors)
