import numpy as np
from calc.par_simple import treasury_par_to_spot_curve_simple

# These are Treasury rates of 1st March 2023, 03/01/2023

par_t = np.array([1,2,3,4, 6,12,24,36,60,84,120,240,360])
par_r = 0.01 * np.array([4.67, 4.82, 4.90, 5.02, 5.20, 5.06, 4.89, 4.61, 4.27, 4.17, 4.01, 4.17, 3.97])


#0, 1, ... 360 elements
spot_r = treasury_par_to_spot_curve_simple(par_t, par_r)
print('tenor  par     spot')
for t, r in zip(par_t, par_r):
    print(f'{t:3d}    {r*100:.2f}    {spot_r[t]*100:.4f}')
