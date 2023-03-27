import numpy as np
import pandas as pd
from calc import LinearParCurveModel
from calc.util import cont_to_biannual

# These are Treasury rates of 1st March 2023, 03/01/2023
tenors = np.array([1, 2, 3, 4, 6, 12, 24, 36, 60, 84, 120, 240, 360])
par_rates = 0.01 * np.array([4.67, 4.82, 4.90, 5.02, 5.20, 5.06, 4.89, 4.61, 4.27, 4.17, 4.01, 4.17, 3.97])

model = LinearParCurveModel()

model.fit(tenors, par_rates)

t = np.arange(13)
s = cont_to_biannual(model.spot_rates(t))
f = model.forward_rates(t)

df = pd.DataFrame(index=t, data={'spot-rates': s, 'forward-rates': f})
print(df)
