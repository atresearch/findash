import pandas as pd
import numpy as np

from calc import (
    LinearLogDFSpotCurveModel,
    LinearParCurveModel,
    LinearSpotCurveModel,
    CubicSplineSpotCurveModel,
    MonoCubicSplineSpotCurveModel,
    QLModel
)

from calc.util import cont_to_biannual

# These are Treasury rates of 1st March 2023, 03/01/2023
tenors = np.array([1, 2, 3, 4, 6, 12, 24, 36, 60, 84, 120, 240, 360])
par_rates = 0.01 * np.array([4.67, 4.82, 4.90, 5.02, 5.20, 5.06, 4.89, 4.61, 4.27, 4.17, 4.01, 4.17, 3.97])


models = {
    #'log-df': LinearLogDFSpotCurveModel(),
    'lin-par': LinearParCurveModel(),
    #'lin-spot': LinearSpotCurveModel(),
    'spline': CubicSplineSpotCurveModel(bc_type=('natural', 'natural')),
    'monosp': MonoCubicSplineSpotCurveModel(),
    'ql': QLModel('2023-03-01')
}

results = pd.DataFrame(index=tenors)

for model_name, model in models.items():
    model.fit(tenors,  par_rates)
    if model_name == 'ql':
        results[model_name] = 100*np.array(model.spot_rates(tenors))
    else:
        results[model_name] = 100*cont_to_biannual(model.spot_rates(tenors))

results['err x100'] = 100*(results['monosp'] - results['ql'])

with pd.option_context('display.float_format', '{:0.4f}'.format):
    print(results)

