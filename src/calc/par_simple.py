import math
import numpy as np

def cont_to_biannual(rc):
    """Convert a continuous rate e^rc to the equivalent biannual rate (1 +rb / 2)^2

    Args:
        rc (float or array/list): continuous interest rate

    Returns:
        float or array/list: biannual interest rate
    """
    return 2 * (np.exp(0.5 * rc) - 1)


def biannual_to_cont(rb):
    """Convert a biannual rate (1 +rb / 2)^2 to the equivalent continuous rate e^rc
 
    Args:
        rb (float or array/list): biannual interest rate

    Returns:
        float or array/list: continuous interest rate
    """
    return 2 * np.log(1 + rb / 2)


def treasury_par_to_spot_le_6m(m, rp):
    """Convert a treasury par rate to a continuous spot rate for tenors <= 6,

    Args:
        m (int): Number of months
        rp (float): Par rate, e.g. 0.04 is 4%
    """
    assert(m <= 6)
    assert(m > 0)
    coupon_cashflow = 100 * rp / 2
    accrual = coupon_cashflow * (6 - m) / 6
    ratio = (100 + accrual) / (100 + coupon_cashflow)
    rc = -np.log(ratio) * 12 / m
    return rc
     

def treasury_par_to_spot_curve_simple(m_arr, rp_arr):
    """US Treasury par to  spot conversion.

    Args:
        m (array[int]): Bond tenors in months.
        r[] (array[float]): Par rates.
    """

    # Some checks
    assert isinstance(m_arr, (list,  np.array)), "m_arr needs to be a list or array."
    assert isinstance(rp_arr, (list,  np.array)), "rp_arr needs to be a list or array."
    assert (len(m_arr) == len(rp_arr)), "m_arr and rp_arr arrays need to have the same length."
    assert (len(m_arr) > 0), "Arrays need to have at least 1 element"

    # The output we are going to fill. And array of 360 monthly continuous spot rates.
    rc = np.zeros(360, dtype=np.float)

    # loop over the list of tenors and par-rates, we also need the index i
    for i in len(m_arr):
        m = m_arr[i]
        rp = rp_arr[i]

        if i > 0:
            m_prev = m_arr[i]
            rp_prev = rp_arr[i]            

        # For short tenors we have this special function
        if m <= 6:
            rc[m] = treasury_par_to_spot_le_6m(m, rp)
        else:
            # todo boostrap, interpolate all the cashflow tenors i * 6m
            pass

        # Interpolate the SPOT curve
        if i == 0:
            # for the first tenor we set all shorter spots to the same value
            rc[0:m] = rc[m]
        else:
            # linear interpolate from previous spot to current 
            rc[m_prev:m+1] = np.linspace(rc[m_prev], rc[m], m - m_prev + 1)





