
VoC_start_date = '2021-05-01' # Date from which to apply the VoC Reff increase
use_linelist = True # If something goes wrong on a day you can set this to True to use the linelist
assume_local_cases_if_unknown = True
start_date = '2021-04-15' # Start date of forecast
num_forecast_days=35 # Number of days after data date to forecast (usually 35)

case_insertion_threshold = 5 # The ratio of true cases to simulation cases below which we insert cases into branching process
use_vaccine_effect = False
use_voc_effect = False
download_google_automatically = False # Will download Google data automatically on run. Set to false for repeated runs.

# Transmission parameters     

# k = 0.1 #  Heterogeneity parameter for a negative binomial offspring distribution

# local_detection = {
#             'NSW':0.9,
#             'QLD':0.9,
#             'SA':0.7,
#             'TAS':0.4,
#             'VIC':0.35,
#             'WA':0.7,
#             'ACT':0.95,
#             'NT':0.95,
#         }

# a_local_detection = {
#             'NSW':0.05,
#             'QLD':0.05,
#             'SA':0.05,
#             'TAS':0.05,
#             'VIC':0.05,
#             'WA':0.05,
#             'ACT':0.7,
#             'NT':0.7,
#         }

# qi_d = {
#             'NSW':0.98,
#             'QLD':0.98,
#             'SA':0.98,
#             'TAS':0.98,
#             'VIC':0.98,
#             'WA':0.98,
#             'ACT':0.98,
#             'NT':0.98,
#         }

#  #alpha_i is impact of importations after April 15th
# alpha_i = {
#             'NSW':1,
#             'QLD':0.1,
#             'SA':0.1,
#             'TAS':0.5,
#             'VIC':1,
#             'WA':0.1,
#             'ACT':0.1,
#             'NT':0.1,
#         }

# Transmission parameters     
k = 0.15 #  Heterogeneity parameter for a negative binomial offspring distribution

# Also known as qs, this is the probability of detecting an symptomatic case. This will go up during major testing drives. Increasing qs increases the observed outbreak. 
local_detection = {
            'NSW':0.95,
            'QLD':0.95,
            'SA':0.95,
            'TAS':0.95,
            'VIC':0.95,
            'WA':0.95,
            'ACT':0.95,
            'NT':0.95,
        }

# Also known as qa, this is the probability of detecting an asymptomatic case.
a_local_detection = {
            'NSW':0.15,
            'QLD':0.1,
            'SA':0.1,
            'TAS':0.1,
            'VIC':0.15,
            'WA':0.1,
            'ACT':0.1,
            'NT':0.1,
        }

qi_d = {
            'NSW':0.98,
            'QLD':0.98,
            'SA':0.98,
            'TAS':0.98,
            'VIC':0.98,
            'WA':0.98,
            'ACT':0.98,
            'NT':0.98,
        }

# alpha_i is impact of importations after April 15th. These have been set to 1 as we not long believe there are significant differences between hotel quarentine effectiveness between states.
alpha_i = {
            'NSW':1,
            'QLD':1,
            'SA':1,
            'TAS':1,
            'VIC':1,
            'WA':1,
            'ACT':1,
            'NT':1,
        }