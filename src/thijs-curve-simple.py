import numpy as np
from calc.par_simple import treasury_par_to_spot_curve_simple
from calc.par_spline import treasury_par_to_spot_curve_spline
from calc.util import cont_to_biannual

# These are Treasury rates of 1st March 2023, 03/01/2023

par_t = np.array([1,2,3,4, 6,12,24,36,60,84,120,240,360])
par_r = 0.01 * np.array([4.67, 4.82, 4.90, 5.02, 5.20, 5.06, 4.89, 4.61, 4.27, 4.17, 4.01, 4.17, 3.97])


#0, 1, ... 360 elements
spot_simple_r = treasury_par_to_spot_curve_simple(par_t, par_r)
spot_simple_r2 = cont_to_biannual(spot_simple_r)

spot_spline_r = treasury_par_to_spot_curve_spline(par_t, par_r)
spot_spline_r2 = cont_to_biannual(spot_spline_r)

print('               SIMPLE    SPLINE   SIMPLE    SPLINE   ')
print('tenor  par     spot_c    spot_c   spot_bi   spot_bi ')
for t, r in zip(par_t, par_r):
    print(f'{t:3d}    {r*100:.2f}    {spot_simple_r[t]*100:.4f}    {spot_spline_r[t]*100:.4f}   {spot_simple_r2[t]*100:.4f}    {spot_spline_r2[t]*100:.4f}')


