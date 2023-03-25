import numpy as np
from scipy import interpolate
from scipy.optimize import minimize


def price_par_bonds_spline(spot_curve, tenors, par_rates, debug=False):
    # price all the bond
    
    bond_prices = []
    
    for tenor, par_rate in zip(tenors, par_rates):

        # points in times of bond cashflows
        cashflow_times = np.arange(tenor, 0, -6)[::-1]

        # the size of the cashflows
        cashflow_amounts = 0.5 * par_rate * np.ones_like(cashflow_times)
        cashflow_amounts[-1] += 1

        # the npv of these cashflows using the spot curve
        cashflow_rates = interpolate.splev(cashflow_times, spot_curve)
        cashflow_discount_factors = np.exp(-cashflow_rates * cashflow_times / 12)

        # clean price (without accruel)
        bond_clean_price = np.sum(cashflow_amounts * cashflow_discount_factors)
        
        # Accruel
        time_since_last_coupon = (6 - tenor) % 6
        accruel = (time_since_last_coupon / 6) * (par_rate / 2)
        
        bond_dirty_price = bond_clean_price - accruel
        
        # add the bond to the list of answers
        bond_prices.append(bond_dirty_price)

        # print details
        if debug:
            print(f'\nBond: tenor={tenor}m  par-rate={par_rate*100:.2f}%')
            print('cashflow_times:',cashflow_times)
            print('cashflow_amounts:',cashflow_amounts)
            print('cashflow_rates (cont):',cashflow_rates)
            print('cashflow_rates (bi):',cont_to_biannual(cashflow_rates))
            print('bond_clean_price:',bond_clean_price)
            print('time_since_last_coupon', time_since_last_coupon)
            print('accruel:',accruel)
            print('bond_dirty_price:',bond_dirty_price)
    
    return bond_prices


def spline_fit_error(spot_rates, tenors, par_rates, tol=1E-3):
    
    # fit a cubic spline
    spot_curve = interpolate.splrep(tenors, spot_rates)

    # price all the bonds
    bond_clean_prices = price_par_bonds_spline(spot_curve, tenors, par_rates)

    #compute errors, bonds prices should be 'par', i.e. 100
    d_prices = np.asarray(bond_clean_prices) * 100 - 100
    rmse = np.mean(d_prices**2)**0.5
    
    # if the error is below tol we can stop, setting rmse to the 0 should do that
    if rmse < tol:
        rmse = 0
    
    return rmse


def treasury_par_to_spot_curve_spline(tenors, par_rates):

    # initial guess for the spot rate
    spot_rates = par_rates.copy()

    ans = minimize(spline_fit_error, spot_rates, (tenors, par_rates), tol=1E-3)

    spot_curve = interpolate.splrep(tenors, ans.x)
    spot_rates = interpolate.splev(np.arange(361), spot_curve)
    return spot_rates