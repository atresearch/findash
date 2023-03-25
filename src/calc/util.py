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