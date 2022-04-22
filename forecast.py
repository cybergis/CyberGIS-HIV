import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import r, pandas2ri
import time
ro.r('''source('forecast_func.R')''')

if __name__ == '__main__':
    pandas2ri.activate()

    forecast_func = ro.globalenv['forecast_func']

    # when no argument is selected, it will do the forecast for all FIPS codes
    st = time.time()

    data_wide = forecast_func(var_names=["illicit_l", "nFedQualifiedHealthCenters_r_l", "linkage"], var_muls=[2, 2, 2])

    # run forecast for all counties
    data_wide = forecast_func(
        var_names=["illicit_l", "nFedQualifiedHealthCenters_r_l", "linkage", "knowledge", "hcv", "syphilis_rate",
                   "opioid_prsc", "hivtst", "HHswSupplemntlSecurityInc_r", "nNHSCPrimaryCareSiteswProv_r_l",
                   "PopinJuvenilleFacilities_r_l", "Persons1864HealthInsurance_r", "prep_rate_l"],
        var_muls=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2])

    print("It took {} to run for all FIPS codes. ".format(time.time()-st))

    print("Python done!")