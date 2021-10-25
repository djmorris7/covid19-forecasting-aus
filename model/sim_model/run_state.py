import sys
from typing import MutableMapping
sys.path.insert(0,'model')
from sim_class_cython import *
from params import start_date, num_forecast_days, ncores, testing_sim  # External parameters
from scenarios import scenarios

import pandas as pd
from sys import argv
from numpy.random import beta, gamma
from tqdm import tqdm
import multiprocessing as mp

# Check for the number of cores on the machine and break early. This is 
# needed to avoid issues for running locally as running with 12 cores
# can result in freezes/crashes 
if mp.cpu_count() < ncores:
    print("=========================")
    print("Machine does not have target number of cores available.")
    print("Might need to turn on_phoenix off...")
    print("Running with: ", mp.cpu_count()/2, " cores.")
    print("=========================")
    ncores = int(mp.cpu_count() / 2)


from timeit import default_timer as timer

if testing_sim:
    n_sims = 100
else: 
    n_sims = int(argv[1])  # number of sims
    
forecast_date = argv[2]  # Date of forecast
state = argv[3] 

# print("Simulating state " + state)

# Get total number of simulation days
end_date = pd.to_datetime(forecast_date, format="%Y-%m-%d") + pd.Timedelta(days=num_forecast_days)
# if state == 'VIC':
#     start_date = pd.to_datetime('2021-08-01') 
#     end_time = (end_date - pd.to_datetime(start_date, format="%Y-%m-%d")).days  # end_time is recorded as a number of days
# else:
#     end_time = (end_date - pd.to_datetime(start_date, format="%Y-%m-%d")).days  # end_time is recorded as a number of days

end_time = (end_date - pd.to_datetime(start_date, format="%Y-%m-%d")).days  # end_time is recorded as a number of days    

case_file_date = pd.to_datetime(forecast_date).strftime("%d%b%Y")  # Convert date to format used in case file

# initialise the number of cases 
# note that these are of the form [import (I), asymptomatic (A), symptomatic (S)]
if start_date == "2020-03-01":
    current = {
        'ACT': [0, 0, 0],
        'NSW': [4, 0, 2],  # 1
        'NT': [0, 0, 0],
        'QLD': [2, 0, 0],
        'SA': [2, 0, 0],
        'TAS': [0, 0, 0],
        'VIC': [2, 0, 0],  # 1
        'WA': [0, 0, 0],
    }
elif start_date == "2020-09-01":
    current = {
        'ACT': [0, 0, 0],
        'NSW': [3, 0, 7],  # 1
        'NT': [0, 0, 0],
        'QLD': [0, 0, 3],
        'SA': [0, 0, 0],
        'TAS': [0, 0, 0],
        'VIC': [0, 0, 60],  # 1
        'WA': [1, 0, 0],
    }
elif start_date == "2020-12-01":
    current = {  # based on locally acquired cases in the days preceding the start date
        'ACT': [0, 0, 0],
        'NSW': [0, 0, 1],
        'NT': [0, 0, 0],
        'QLD': [0, 0, 1],
        'SA': [0, 0, 0],
        'TAS': [0, 0, 0],
        'VIC': [0, 0, 0],
        'WA': [0, 0, 0],
    }
elif start_date == '2021-04-01':
    current = {  # based on locally acquired cases in the days preceding the start date
        'ACT': [3, 0, 0],
        'NSW': [3, 0, 10],
        'NT': [0, 0, 0],
        'QLD': [14, 0, 1],
        'SA': [0, 0, 0],
        'TAS': [0, 0, 0],
        'VIC': [0, 0, 3],
        'WA': [18, 0, 2],
    }
elif start_date == '2021-05-15':
    current = {  # based on locally acquired cases in the days preceding the start date
        'ACT': [3, 0, 0],
        'NSW': [3, 0, 10],
        'NT': [0, 0, 0],
        'QLD': [14, 0, 1],
        'SA': [0, 0, 0],
        'TAS': [0, 0, 0],
        'VIC': [0, 0, 3],
        'WA': [18, 0, 2],
    }
else:
    current = {  # based on locally acquired cases in the days preceding the start date
        'ACT': [3, 0, 0],
        'NSW': [3, 0, 4],
        'NT': [0, 0, 0],
        'QLD': [14, 0, 1],
        'SA': [0, 0, 0],
        'TAS': [0, 0, 0],
        'VIC': [0, 0, 0],
        'WA': [18, 0, 2],
    }


####### Create simulation.py object ########

VoC_flag = 'Delta'

forecast_object = Forecast(current[state],
                           state, 
                           start_date, 
                           forecast_date=forecast_date,
                           cases_file_date=case_file_date,
                           VoC_flag=VoC_flag, 
                           scenario=scenarios[state], 
                           end_time = end_time)

############ Run Simulations in parallel and return ############


def worker(arg):
    obj, methname = arg[:2]
    return getattr(obj, methname)(*arg[2:])

if __name__ == "__main__":
    # initialise arrays

    import_sims = np.zeros(shape=(end_time, n_sims), dtype=float)
    import_sims_obs = np.zeros_like(import_sims)

    import_inci = np.zeros_like(import_sims)
    import_inci_obs = np.zeros_like(import_sims)

    asymp_inci = np.zeros_like(import_sims)
    asymp_inci_obs = np.zeros_like(import_sims)

    symp_inci = np.zeros_like(import_sims)
    symp_inci_obs = np.zeros_like(import_sims)

    bad_sim = np.zeros(shape=(n_sims), dtype=int)

    travel_seeds = np.zeros(shape=(end_time, n_sims), dtype=int)
    travel_induced_cases = np.zeros_like(travel_seeds)

    forecast_object.read_in_cases()

    start_timer = timer()

    pool = mp.Pool(ncores)
    with tqdm(total=n_sims, leave=False, smoothing=0, miniters=1000) as pbar:
        for cases, obs_cases, param_dict in pool.imap_unordered(worker,[(forecast_object, 'simulate', end_time, n, n) for n in range(n_sims)]):
            # cycle through all results and record into arrays
            n = param_dict['num_of_sim']
            if param_dict['bad_sim']:
                # bad_sim True
                bad_sim[n] = 1

            # record cases appropriately
            import_inci[:, n] = cases[:, 0]
            asymp_inci[:, n] = cases[:, 1]
            symp_inci[:, n] = cases[:, 2]

            import_inci_obs[:, n] = obs_cases[:, 0]
            asymp_inci_obs[:, n] = obs_cases[:, 1]
            symp_inci_obs[:, n] = obs_cases[:, 2]
            pbar.update()

    pool.close()
    pool.join()

    # convert arrays into df
    results = {
        'imports_inci': import_inci,
        'imports_inci_obs': import_inci_obs,
        'asymp_inci': asymp_inci,
        'asymp_inci_obs': asymp_inci_obs,
        'symp_inci': symp_inci,
        'symp_inci_obs': symp_inci_obs,
        'total_inci_obs': symp_inci_obs + asymp_inci_obs,
        'total_inci': symp_inci + asymp_inci,
        'all_inci': symp_inci + asymp_inci + import_inci,
        'bad_sim': bad_sim
    }
    
    print("Number of bad sims is %i" % sum(bad_sim))
    # results recorded into parquet as dataframe
    df = forecast_object.to_df(results)
    
    end_timer = timer()
    time_for_sim = end_timer-start_timer

    print(state, " took: %f" %time_for_sim)
    
# if __name__ == '__main__':
    # import cProfile, pstats
    # profiler = cProfile.Profile()
    # profiler.enable()
    # main()
    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats('ncalls')
    # stats.print_stats()
    # stats.dump_stats('stats_file.prof')
    
    
    