import math
import numpy as np


def treasury_par_to_spot_le_6m(m, rp):
    """Convert a treasury par rate to a continuous spot rate for tenors <= 6,

    Args:
        m (int): Number of months
        rp (float): Par rate, e.g. 0.04 is 4%
    """
    assert (m <= 6)
    assert (m > 0)
    coupon_cashflow = 100 * rp / 2
    accrual = coupon_cashflow  * (6 - m) / 6
    ratio = (100 + accrual) / (100 + coupon_cashflow)
    rc = -np.log(ratio) * 12 / m
    return rc
  

def treasury_par_to_spot_ge_6m(coupon_tenors, coupon_spot_rates, par_rate):
    if len(coupon_tenors) > 0:
        t = coupon_tenors[-1] / 12 + .5
        coupon_npv_sum = par_rate / 2 * np.sum( np.exp(-coupon_spot_rates * coupon_tenors / 12))
    else:
        t = .5
        coupon_npv_sum = 0
    enrt = (1 - coupon_npv_sum) / (1 + par_rate / 2)
    r = -np.log(enrt) / t
    return r


def treasury_par_to_spot_curve_simple(tenors, par_rates):
    """US Treasury par to  spot conversion.

    Args:
        m (array[int]): Bond tenors in months.
        r[] (array[float]): Par rates.
    """

    tenors = np.asarray(tenors)
    par_rates = np.asarray(par_rates)

    # Some checks
    assert isinstance(tenors, (list,  np.ndarray)), f"m_arr needs to be a list or array but is a {type(tenors)}."
    assert isinstance(par_rates, (list,  np.ndarray)), f"rp_arr needs to be a list or array but is a {type(par_rates)}."
    assert (len(tenors) == len(par_rates)), "m_arr and rp_arr arrays need to have the same length."
    assert (len(tenors) > 0), "Arrays need to have at least 1 element"
    

    
    # First count the nr tenors < 6m
    num_tenors_le_6m = sum(1 for t in tenors if t < 6)

    # Select the tenors & par-rates < 6m
    short_tenors = tenors[0:num_tenors_le_6m]
    short_par_rates = par_rates[0:num_tenors_le_6m]

    # Calculate the spot-rates for these tenors
    short_spot_rates = [
        treasury_par_to_spot_le_6m(t, r)
        for t, r in zip(short_tenors, short_par_rates)
    ]

    # Create a list of tenors for all coupons (all 6m multiples)
    coupon_tenors = np.arange(6, 366, 6) #  {6, 12, ..., 354, 360}

    # interpolate par-rates so that we have a par rate for all 6m multiples
    par_rates = np.interp(coupon_tenors, tenors, par_rates)

    # placeholder for spot calculation results
    coupon_spot_rates = np.zeros_like(coupon_tenors, dtype=float)

    for i in range(len(coupon_tenors)):
        coupon_spot_rates[i] = treasury_par_to_spot_ge_6m(
            coupon_tenors[:i], 
            coupon_spot_rates[:i],
            par_rates[i]
        )

    # merge the short and long spot curve
    new_tenors = np.concatenate([short_tenors, coupon_tenors])
    new_rates = np.concatenate([short_spot_rates, coupon_spot_rates])

    # Return a monthly-resolution spot rate
    return np.interp(range(0, 361), new_tenors, new_rates)

