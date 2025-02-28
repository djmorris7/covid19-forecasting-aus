###
# Run EpyReff on NNDSS data
###

from scipy.stats import gamma
from sys import argv
import sys

sys.path.insert(0, "TP_model")
sys.path.insert(0, "TP_model/EpyReff")
# this is not used in the estimation routine, it just lets the plot know what we ignore
from params import (
    truncation_days,
    sim_start_date,
    use_TP_adjustment,
    scale_rd,
    shape_rd,
    scale_gen,
    shape_gen,
    scale_inc,
    shape_inc,
    scale_inc_omicron,
    shape_inc_omicron,
    inc_disc_pmf,
    inc_omicron_disc_pmf,
    gen_disc_pmf,
    gen_omicron_disc_pmf,
)
from epyreff import *
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import matplotlib

matplotlib.use("Agg")

# parameters
tau = 4
prior_a = 1
prior_b = 3
trunc_days = 21
shift = 0

date = argv[1]
dt_date = pd.to_datetime(date, format="%Y-%m-%d")
file_date = dt_date.strftime("%Y-%m-%d") 

# uncomment this if you wanna see the time distributions    
plot_time = False

# read in case file data
print("=============")
print("Running EpyReff on NNDSS data for", dt_date.strftime("%d%b%Y"))
print("=============")

df_interim = read_cases_lambda(dt_date.strftime("%d%b%Y"))

# generate dataframe with id_vars date and state, variable SOURCE and number of cases
df_linel = tidy_cases_lambda(df_interim, remove_territories=False)

# number of samples to draw
samples = 500

for strain in ("Delta", "Omicron"):
    
    print("=============")
    print("Running EpyReff for", strain)
    print("=============")
    
    R_summary_states = {}
    dates = {}
    df = pd.DataFrame()
    df_R_samples = pd.DataFrame()
    R_store = {}

    # NOTE: this is by far not optimal but since it's such a small part of the procedure
    # we haven't modified the previous code too much outside of treating things as vectors.
    for rep in tqdm(range(samples)):
        if strain == "Omicron":
            (shape_inc_actual, scale_inc_actual) = (shape_inc_omicron, scale_inc_omicron)
            inc_disc_actual_pmf = inc_omicron_disc_pmf
            gen_disc_actual_pmf = gen_omicron_disc_pmf
        else:
            (shape_inc_actual, scale_inc_actual) = (shape_inc, scale_inc)
            inc_disc_actual_pmf = inc_disc_pmf
            gen_disc_actual_pmf = gen_disc_pmf
            
        # generate realisation of infection dates from notification dates
        df_inf = draw_inf_dates(
            df_linel,
            inc_disc_pmf=inc_disc_pmf, 
        )

        # reindex dataframe to include all dates,
        # return df with index (STATE, INFECTION_DATE, SOURCE), columns are samples
        df_inc_zeros = index_by_infection_date(df_inf)

        # get all lambdas
        lambda_dict = lambda_all_states(
            df_inc_zeros,
            gen_disc_pmf=gen_disc_actual_pmf,
            trunc_days=trunc_days,
        )

        states = [*df_inc_zeros.index.get_level_values("STATE").unique()]

        for state in states:
            lambda_state = lambda_dict[state][:, 0]
            df_state_I = df_inc_zeros.xs((state, "local"), level=("STATE", "SOURCE"))

            cases_by_infection = df_state_I.n_cases.values

            # keep track of days indexed in the dataframe
            first_date_index_new = df_state_I.index[0]
            last_date_index_new = df_state_I.index[-1]

            # store sampled Reffs
            if rep == 0:
                # store the dates
                dates[state] = df_state_I.index.values[trunc_days - 1 + tau :]
                first_date_index_min = first_date_index_new
                last_date_index_max = last_date_index_new
            else:
                first_date_index_old = min(first_date_index_min, first_date_index_new)

            # get Reproduciton numbers
            (a, b, R) = Reff_from_case(
                cases_by_infection, 
                lambda_state, 
                prior_a=prior_a, 
                prior_b=prior_b, 
                tau=tau,
            )

            if first_date_index_new > first_date_index_min:
                R = np.append([0] * (first_date_index_new - first_date_index_min).days, R)
            elif first_date_index_new < first_date_index_min:
                R = R[(first_date_index_min - first_date_index_new).days :]

            if last_date_index_new < last_date_index_max:
                R = np.append(R, [0] * (last_date_index_max - last_date_index_new).days)
            elif last_date_index_new > last_date_index_max:
                R = R[: -(last_date_index_new - last_date_index_max).days]

            # store sampled Reffs
            if rep == 0:
                R_store[state] = R
            else:
                R_store[state] = np.vstack([R_store[state], R])

    # to interface with the previous code we need to transpose R_store
    for state in states:
        R_store[state] = R_store[state].T

    # now we loop over the states and calculate summaries
    for state in states:
        df_state_I = df_inc_zeros.xs((state, "local"), level=("STATE", "SOURCE"))

        # extract latest R
        R = R_store[state]

        if use_TP_adjustment:
            # temporarily store important information
            temp = pd.DataFrame.from_dict(R_store[state])
            temp["INFECTION_DATES"] = dates[state]
            temp["STATE"] = state
            df_R_samples = df_R_samples.append(temp, ignore_index=True)

        # summarise for plots and file printing
        R_summary_states[state] = generate_summary(R)
        temp = pd.DataFrame.from_dict(R_summary_states[state])
        temp["INFECTION_DATES"] = dates[state]
        temp["STATE"] = state
        # temp.index = pd.MultiIndex.from_product(([state], dates[state]))
        df = df.append(temp, ignore_index=True)

    # make folder to record files
    os.makedirs("results/EpyReff/", exist_ok=True)

    if plot_time:
        # plot assumed distributions
        inc_period = np.random.gamma(shape_inc, scale_inc, size=1000)
        rep_delay = np.random.gamma(shape_rd, scale_rd, size=1000)

        # generation interval discretised
        # Find midpoints for discretisation
        xmids = [x + shift for x in range(trunc_days + 1)]
        # double check parameterisation of scipy
        gamma_vals = gamma.pdf(xmids, a=shape_gen, scale=scale_gen)
        # renormalise the pdf
        disc_gamma = gamma_vals / sum(gamma_vals)
        ws = disc_gamma[:trunc_days]

        fig, ax = plt.subplots(figsize=(12, 18), nrows=3, sharex=True)

        ax[0].hist(rep_delay, bins=50, density=True)
        ax[0].set_title("Reporting Delay")
        ax[1].hist(inc_period, bins=50, density=True)
        ax[1].set_title("Incubation Period")
        ax[2].bar(xmids[:-1], height=ws, width=1)
        ax[2].set_title("Generation Interval")

        plt.savefig(
            "figs/Time_distributions" + file_date + "tau_" + str(tau) + ".png", dpi=400
        )

    # saving files
    if strain == "Omicron":
        file_name_start = "results/EpyReff/Reff_omicron"
    else:
        file_name_start = "results/EpyReff/Reff_delta"
        
    # save the summary Reff's
    df.to_csv(file_name_start + file_date + "tau_" + str(tau) + ".csv", index=False)
    
    # we tile the Reff's to the same size (2000) for the TP forecasts 
    df_Reff_samples = np.tile(df_R_samples.iloc[:, :-2].to_numpy(), 4)
    df_Reff_full = pd.DataFrame(df_Reff_samples, columns=[str(n) for n in range(2000)])
    df_Reff_full["INFECTION_DATES"] = df_R_samples["INFECTION_DATES"]
    df_Reff_full["STATE"] = df_R_samples["STATE"]
    df_Reff_full.to_csv(
        file_name_start + "_samples" + file_date + "tau_" + str(tau) + ".csv", index=False
    )

    # plot all the estimates
    file_date_updated = dt_date
    file_date_updated = file_date_updated.strftime("%Y-%m-%d")

    # read in an adjusted file
    df_NNDSS = read_in_NNDSS(dt_date.strftime("%d%b%Y"), apply_delay_at_read=True)
    df_interim = df_NNDSS[["date_inferred", "STATE", "imported", "local"]]

    # plot the observed cases each day and overlay the effective reproduction number.
    fig, ax = plot_all_states(
        R_summary_states,
        df_interim,
        dates,
        start=sim_start_date,
        end=file_date_updated,
        save=True,
        tau=tau,
        date=date,
        nowcast_truncation=-truncation_days,
        omicron_Reff=(strain == "Omicron"),
    )
    plt.close()
