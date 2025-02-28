import os
import sys
from numpy.core.numeric import zeros_like
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use("seaborn-poster")
# I hate this too but it allows everything to use the same helper functions.
sys.path.insert(0, "TP_model")
from helper_functions import read_in_NNDSS
from Reff_constants import *

def read_in_posterior(date):
    """
    read in samples from posterior from inference
    """
    df = pd.read_hdf(
        "results/"
        + date 
        + "/soc_mob_posterior" 
        + date 
        + ".h5", 
        key="samples"
    )

    return df


def read_in_google(Aus_only=True, local=True, moving=False, moving_window=7):
    """
    Read in the Google data set
    """
    if local:
        if type(local) == str:
            df = pd.read_csv(local, parse_dates=["date"])
        elif type(local) == bool:
            local = "data/Global_Mobility_Report.csv"
            df = pd.read_csv(local, parse_dates=["date"])
    else:
        # Download straight from the web
        df = pd.read_csv(
            "https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv",
            parse_dates=["date"],
        )
        # Make it save automatically.
        df.to_csv("data/Global_Mobility_Report.csv", index=False)

    if Aus_only:
        df = df.loc[df.country_region_code == "AU"]
        # Change state column to state initials
        df["state"] = df.sub_region_1.map(
            lambda x: states_initials[x] if not pd.isna(x) else "AUS"
        )

    df = df.loc[df.sub_region_2.isna()]
    if moving:
        # generate moving average columns in reverse
        df = df.sort_values(by="date")
        mov_values = []
        for val in value_vars:
            mov_values.append(val[:-29] + "_7days")
            # df[mov_values[-1]] = df.groupby(["state"])[val].transform(
            #     lambda x: x[::-1].rolling(moving_window, 1, center=True).mean()[::-1]
            # )  # minimumnumber of 1

            # # minimum of moving_window days for std, forward fill the rest
            # df[mov_values[-1] + "_std"] = df.groupby(["state"])[val].transform(
            #     lambda x: x[::-1].rolling(moving_window, moving_window, center=True).std()[::-1]
            # )
            
            # MA was taken in reverse, what about when we do it normally?
            df[mov_values[-1]] = df.groupby(["state"])[val].transform(
                lambda x: x.rolling(moving_window, 1, center=True).mean()
            )  # minimumnumber of 1

            # minimum of moving_window days for std, forward fill the rest
            df[mov_values[-1] + "_std"] = df.groupby(["state"])[val].transform(
                lambda x: x.rolling(moving_window, moving_window, center=True).std()
            )
            # fill final values as std doesn't work with single value
            df[mov_values[-1] + "_std"] = df.groupby("state")[
                mov_values[-1] + "_std"
            ].fillna(method="ffill")

    # show latest date
    print("Latest date in Google indices " + str(df.date.values[-1]))
    
    name_addon = "ma" * moving + (1 - moving) * "standard"
    df.to_csv("results/mobility_" + name_addon + ".csv")
    
    return df


def predict_plot(
    samples,
    df,
    moving=True,
    grocery=True,
    rho=None,
    second_phase=False,
    third_phase=False,
    third_plot_type="combined",
):
    """
    Produce posterior predictive plots for all states using the inferred mu_hat. This should run 
    regardless of the form of the model as it only requires the mu_hat parameter which is 
    calculated inside stan (the TP model fitted to the Reff). 
    """

    value_vars = [
        "retail_and_recreation_percent_change_from_baseline",
        "grocery_and_pharmacy_percent_change_from_baseline",
        "parks_percent_change_from_baseline",
        "transit_stations_percent_change_from_baseline",
        "workplaces_percent_change_from_baseline",
        "residential_percent_change_from_baseline",
    ]
    value_vars.remove("residential_percent_change_from_baseline")

    if not grocery:
        value_vars.remove("grocery_and_pharmacy_percent_change_from_baseline")
    if moving:
        value_vars = [val[:-29] + "_7days" for val in value_vars]

    # all states
    fig, ax = plt.subplots(figsize=(15, 12), ncols=4, nrows=2, sharex=True, sharey=True)

    states = sorted(list(states_initials.keys()))

    if not third_phase:
        states.remove("Northern Territory")
        states.remove("Australian Capital Territory")

    # no R_eff modelled for these states, skip
    # counter for brho_v
    pos = 0
    for i, state in enumerate(states):

        df_state = df.loc[df.sub_region_1 == state]
        if second_phase:
            df_state = df_state.loc[df_state.is_sec_wave == 1]
        elif third_phase:
            df_state = df_state.loc[df_state.is_third_wave == 1]

        # directly plot the fitted TP values 
        states_to_fitd = {s: i + 1 for i, s in enumerate(rho)}
        
        if not second_phase and not third_phase:
            mu_hat = samples[
                [
                    "mu_hat["
                    + str(j + 1)
                    + ","
                    + str(states_to_fitd[states_initials[state]])
                    + "]"
                    for j in range(df_state.shape[0])
                ]
            ].values.T
        elif second_phase:
            mu_hat = samples[
                [
                    "mu_hat_sec[" + str(j + 1) + "]"
                    for j in range(
                        pos,
                        pos
                        + df.loc[
                            df.state == states_initials[state]
                        ].is_sec_wave.sum(),
                    )
                ]
            ].values.T
            pos = (
                pos
                + df.loc[
                    df.state == states_initials[state]
                ].is_sec_wave.sum()
            )
        elif third_phase:
            if third_plot_type == "combined":
                mu_hat = samples[
                    [
                        "mu_hat_third[" + str(j + 1) + "]"
                        for j in range(
                            pos,
                            pos
                            + df.loc[
                                df.state == states_initials[state]
                            ].is_third_wave.sum(),
                        )
                    ]
                ].values.T
                pos = (
                    pos
                    + df.loc[
                        df.state == states_initials[state]
                    ].is_third_wave.sum()
                )
            elif third_plot_type == "delta":
                mu_hat = samples[
                    [
                        "mu_hat_delta_only[" + str(j + 1) + "]"
                        for j in range(
                            pos,
                            pos
                            + df.loc[
                                df.state == states_initials[state]
                            ].is_third_wave.sum(),
                        )
                    ]
                ].values.T
                pos = (
                    pos
                    + df.loc[
                        df.state == states_initials[state]
                    ].is_third_wave.sum()
                )
            elif third_plot_type == "omicron":
                mu_hat = samples[
                    [
                        "mu_hat_omicron_only[" + str(j + 1) + "]"
                        for j in range(
                            pos,
                            pos
                            + df.loc[
                                df.state == states_initials[state]
                            ].is_omicron_wave.sum(),
                        )
                    ]
                ].values.T
                pos = (
                    pos
                    + df.loc[
                        df.state == states_initials[state]
                    ].is_omicron_wave.sum()
                )
            
        
        df_hat = pd.DataFrame(mu_hat.T)
        
        # df_hat.to_csv('mu_hat_' + state + '.csv')

        if states_initials[state] not in rho:
            if i // 4 == 1:
                ax[i // 4, i % 4].tick_params(axis="x", rotation=90)
            continue
        
        if not third_phase: 
            # plot actual R_eff
            ax[i // 4, i % 4].plot(
                df_state.date, df_state["mean"], label="$R_{eff}$", color="C1"
            )
            ax[i // 4, i % 4].fill_between(
                df_state.date, df_state["bottom"], df_state["top"], color="C1", alpha=0.3
            )
            ax[i // 4, i % 4].fill_between(
                df_state.date, df_state["lower"], df_state["upper"], color="C1", alpha=0.3
            )
        elif third_phase:
            if third_plot_type in ("combined", "omicron"):
                # plot actual R_eff
                ax[i // 4, i % 4].plot(
                    df_state.date, df_state["mean_omicron"], label="$R_{eff}$", color="C1"
                )
                ax[i // 4, i % 4].fill_between(
                    df_state.date, 
                    df_state["bottom_omicron"], 
                    df_state["top_omicron"], 
                    color="C1", 
                    alpha=0.3
                )
                ax[i // 4, i % 4].fill_between(
                    df_state.date, 
                    df_state["lower_omicron"], 
                    df_state["upper_omicron"], 
                    color="C1", 
                    alpha=0.3
                )
            else:
                # plot actual R_eff
                ax[i // 4, i % 4].plot(
                    df_state.date, df_state["mean"], label="$R_{eff}$", color="C1"
                )
                ax[i // 4, i % 4].fill_between(
                    df_state.date, 
                    df_state["bottom"], 
                    df_state["top"], 
                    color="C1", 
                    alpha=0.3
                )
                ax[i // 4, i % 4].fill_between(
                    df_state.date, 
                    df_state["lower"], 
                    df_state["upper"], 
                    color="C1", 
                    alpha=0.3
                )
            
            
        ax[i // 4, i % 4].plot(
            df_state.date, df_hat.quantile(0.5, axis=0), label="$\hat{\mu}$", color="C0"
        )
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_hat.quantile(0.25, axis=0),
            df_hat.quantile(0.75, axis=0),
            color="C0",
            alpha=0.3,
        )
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_hat.quantile(0.05, axis=0),
            df_hat.quantile(0.95, axis=0),
            color="C0",
            alpha=0.3,
        )
        ax[i // 4, i % 4].set_title(state)
        # grid line at R_eff =1
        ax[i // 4, i % 4].axhline(1, ls="--", c="k", lw=1)
        ax[i // 4, i % 4].set_yticks([0, 1, 2], minor=False)
        ax[i // 4, i % 4].set_yticklabels([0, 1, 2], minor=False)
        ax[i // 4, i % 4].yaxis.grid(which="minor", linestyle="--", color="black", linewidth=2)
        ax[i // 4, i % 4].set_ylim((0, 2.5))
        
        if i // 4 == 1:
            ax[i // 4, i % 4].tick_params(axis="x", rotation=90)

    plt.legend()
    
    return ax


def predict_multiplier_plot(samples, df, param=""):
    """
    Produce posterior predictive plots for all states of the micro and macro factors. This should 
    enable us to look into the overall factor multiplying TP at any given time. 
    """

    # all states
    fig, ax = plt.subplots(figsize=(15, 12), ncols=4, nrows=2, sharex=True, sharey=True)

    states = sorted(list(states_initials.keys()))
    
    # dictionary for mapping between plot type and variable name
    factor_dict = {
        "micro": "micro_factor", 
        "macro": "macro_factor",
        "susceptibility": "sus_dep_factor"
    }
    
    pos = 0
    for i, state in enumerate(states):

        df_state = df.loc[df.sub_region_1 == state]
        df_state = df_state.loc[df_state.is_third_wave == 1]

        factor = samples[
            [
                factor_dict[param] + "[" + str(j + 1) + "]"
                for j in range(
                    pos,
                    pos
                    + df.loc[
                        df.state == states_initials[state]
                    ].is_third_wave.sum(),
                )
            ]
        ].values.T
        pos = (
            pos
            + df.loc[
                df.state == states_initials[state]
            ].is_third_wave.sum()
        )   
        
        df_hat = pd.DataFrame(factor.T)
        
        # df_hat.to_csv('mu_hat_' + state + '.csv')
        ax[i // 4, i % 4].plot(df_state.date, df_hat.quantile(0.5, axis=0), color="C0")
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_hat.quantile(0.25, axis=0),
            df_hat.quantile(0.75, axis=0),
            color="C0",
            alpha=0.3,
        )
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_hat.quantile(0.05, axis=0),
            df_hat.quantile(0.95, axis=0),
            color="C0",
            alpha=0.3,
        )
        ax[i // 4, i % 4].set_title(state)
        ax[i // 4, i % 4].set_yticks([0, 0.25, 0.5, 0.75, 1, 1.25], minor=False)
        ax[i // 4, i % 4].set_yticklabels([0, 0.25, 0.5, 0.75, 1, 1.25], minor=False)
        ax[i // 4, i % 4].axhline(1, ls="--", c="k", lw=1)
        
        if i // 4 == 1:
            ax[i // 4, i % 4].tick_params(axis="x", rotation=90)

    plt.legend()
    
    return ax


def macro_factor_plots(samples, df):
    """
    Produce posterior predictive plots for all states of the micro and macro factors. This should 
    enable us to look into the overall factor multiplying TP at any given time. 
    """

    # all states
    fig, ax = plt.subplots(figsize=(15, 12), ncols=4, nrows=2, sharex=True, sharey=True)

    states = sorted(list(states_initials.keys()))
    
    # dictionary for mapping between plot type and variable name
    factor_dict = {
        "micro": "micro_factor", 
        "macro": "macro_factor",
        "susceptibility": "sus_dep_factor"
    }
    
    pos = 0
    for i, state in enumerate(states):

        df_state = df.loc[df.sub_region_1 == state]
        df_state = df_state.loc[df_state.is_third_wave == 1]

        data_factor = samples[
            [
                "macro_level_data[" + str(j + 1) + "]"
                for j in range(
                    pos,
                    pos
                    + df.loc[
                        df.state == states_initials[state]
                    ].is_third_wave.sum(),
                )
            ]
        ].values.T
        
        inferred_factor = samples[
            [
                "macro_level_inferred[" + str(j + 1) + "]"
                for j in range(
                    pos,
                    pos
                    + df.loc[
                        df.state == states_initials[state]
                    ].is_third_wave.sum(),
                )
            ]
        ].values.T
        pos = (
            pos
            + df.loc[
                df.state == states_initials[state]
            ].is_third_wave.sum()
        )   
        
        df_data = pd.DataFrame(data_factor.T)
        df_inferred = pd.DataFrame(inferred_factor.T)
        
        # df_hat.to_csv('mu_hat_' + state + '.csv')
        ax[i // 4, i % 4].plot(df_state.date, df_data.quantile(0.5, axis=0), color="C0")
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_data.quantile(0.25, axis=0),
            df_data.quantile(0.75, axis=0),
            color="C0",
            alpha=0.3,
        )
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_data.quantile(0.05, axis=0),
            df_data.quantile(0.95, axis=0),
            color="C0",
            alpha=0.3,
        )
        
        ax[i // 4, i % 4].plot(df_state.date, df_inferred.quantile(0.5, axis=0), color="C1")
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_inferred.quantile(0.25, axis=0),
            df_inferred.quantile(0.75, axis=0),
            color="C1",
            alpha=0.3,
        )
        ax[i // 4, i % 4].fill_between(
            df_state.date,
            df_inferred.quantile(0.05, axis=0),
            df_inferred.quantile(0.95, axis=0),
            color="C1",
            alpha=0.3,
        )
        ax[i // 4, i % 4].set_title(state)
        ax[i // 4, i % 4].set_yticks([0, 0.25, 0.5, 0.75, 1, 1.25], minor=False)
        ax[i // 4, i % 4].set_yticklabels([0, 0.25, 0.5, 0.75, 1, 1.25], minor=False)
        ax[i // 4, i % 4].axhline(1, ls="--", c="k", lw=1)
        
        if i // 4 == 1:
            ax[i // 4, i % 4].tick_params(axis="x", rotation=90)

    plt.legend()
    
    return ax


def plot_adjusted_ve(
    data_date,
    samples_mov_gamma,
    states,
    vaccination_by_state,
    third_states,
    third_date_range,
    ve_samples,
    ve_idx_ranges,
    figs_dir,
    strain,
):

    """
    A function to process the inferred VE. This will save an updated timeseries which 
    is the mean posterior estimates.
    """

    fig, ax = plt.subplots(figsize=(15, 12), ncols=2, nrows=4, sharey=True, sharex=True)
    # temporary state vector

    # make a dataframe for the adjusted vacc_ts
    df_vacc_ts_adjusted = pd.DataFrame()

    # for i, state in enumerate(third_states):
    for i, state in enumerate(states):
        # for i, state in enumerate(states_tmp):
        # grab states vaccination data
        vacc_ts_data = vaccination_by_state.loc[state]

        # apply different vaccine form depending on if NSW
        if state in third_states:
            # get the sampled vaccination effect (this will be incomplete as it's only 
            # over the fitting period)
            vacc_tmp = ve_samples.iloc[ve_idx_ranges[state], :]
            # get before and after fitting and tile them
            vacc_ts_data_before = pd.concat(
                [vacc_ts_data.loc[vacc_ts_data.index < third_date_range[state][0]]]
                * samples_mov_gamma.shape[0],
                axis=1,
            )
            vacc_ts_data_after = pd.concat(
                [vacc_ts_data.loc[vacc_ts_data.index > third_date_range[state][-1]]]
                * samples_mov_gamma.shape[0],
                axis=1,
            )
            # rename columns for easy merging
            vacc_ts_data_before.columns = vacc_tmp.columns
            vacc_ts_data_after.columns = vacc_tmp.columns
            # merge in order
            vacc_ts = pd.concat(
                [vacc_ts_data_before, vacc_tmp, vacc_ts_data_after],
                axis=0,
                ignore_index=True,
            )
            vacc_ts.set_index(vacc_ts_data.index[: vacc_ts.shape[0]], inplace=True)

        else:
            # just tile the data
            vacc_ts = pd.concat(
                [vacc_ts_data] * samples_mov_gamma.shape[0],
                axis=1,
            )
            # reset the index to be the dates for easier information handling
            vacc_ts.set_index(vacc_ts_data.index, inplace=True)
            # need to name columns samples for consistent indexing
            vacc_ts.columns = range(0, samples_mov_gamma.shape[0])

        dates = vacc_ts.index
        vals = vacc_ts.median(axis=1).values
        state_vec = np.repeat([state], vals.shape[0])
        df_vacc_ts_adjusted = pd.concat(
            [
                df_vacc_ts_adjusted,
                pd.DataFrame({"state": state_vec, "date": dates, "effect": vals}),
            ]
        )

        # create zero array to fill in with the full vaccine effect model
        vacc_eff = np.zeros_like(vacc_ts)

        # Note that in here we apply the entire sample to the vaccination data 
        # to create a days by samples array
        for ii in range(vacc_eff.shape[0]):
            vacc_eff[ii] = vacc_ts.iloc[ii, :]

        row = i % 4
        col = i // 4

        ax[row, col].plot(
            dates,
            vaccination_by_state.loc[state][: dates.shape[0]].values,
            label="data",
            color="C1",
        )
        ax[row, col].plot(dates, np.median(vacc_eff, axis=1), label="fit", color="C0")
        ax[row, col].fill_between(
            dates,
            np.quantile(vacc_eff, 0.25, axis=1),
            np.quantile(vacc_eff, 0.75, axis=1),
            color="C0",
            alpha=0.4,
        )
        ax[row, col].fill_between(
            dates,
            np.quantile(vacc_eff, 0.05, axis=1),
            np.quantile(vacc_eff, 0.95, axis=1),
            color="C0",
            alpha=0.4,
        )
        # plot the start and end of the fitting
        if state in third_states:
            ax[row, col].axvline(third_date_range[state][0], ls="--", color="red", lw=1)
            ax[row, col].axvline(third_date_range[state][-1], ls="--", color="red", lw=1)
        ax[row, col].set_title(state)
        ax[row, col].tick_params(axis="x", rotation=90)

    ax[1, 0].set_ylabel("reduction in TP from vaccination")

    df_vacc_ts_adjusted.to_csv(
        "results/" 
        + data_date.strftime("%Y-%m-%d") 
        + "/adjusted_vaccine_ts_"
        + strain
        + data_date.strftime("%Y-%m-%d")
        + ".csv",
        index=False,
    )

    plt.savefig(
        figs_dir
        + data_date.strftime("%Y-%m-%d")
        + "_"
        + strain
        + "_ve_reduction_in_TP.png",
        dpi=144,
    )

    # remove plots from memory
    fig.clear()
    plt.close(fig)

    return None


def read_in_cases(
    case_file_date, 
    apply_delay_at_read=False, 
    apply_inc_at_read=False,
):
    """
    Read in NNDSS data and from data, find rho
    """
    
    df_NNDSS = read_in_NNDSS(
        case_file_date,
        apply_delay_at_read=apply_delay_at_read,
        apply_inc_at_read=apply_inc_at_read,
    )

    df_state = (
        df_NNDSS[["date_inferred", "STATE", "imported", "local"]]
        .groupby(["STATE", "date_inferred"])
        .sum()
    )

    df_state["rho"] = [
        0 if (i + l == 0) else i / (i + l)
        for l, i in zip(df_state.local, df_state.imported)
    ]

    return df_state


def remove_sus_from_Reff(strain, data_date):
    """
    This removes the inferred susceptibility depletion from the Reff estimates out of EpyReff. 
    The inferred Reff = S(t) * Reff_1 where S(t) is the effect of susceptible depletion (i.e. a 
    factor between 0 and 1) and Reff_1 is the Reff without the effect of a reducing susceptibility 
    pool.
    """
    from params import pop_sizes

    data_date = pd.to_datetime(data_date)
    # read in Reff samples
    df_Reff = pd.read_csv(
        "results/EpyReff/Reff_" 
        + strain 
        + "_samples" 
        + data_date.strftime("%Y-%m-%d")
        + "tau_4.csv",
        parse_dates=["INFECTION_DATES"],
    )

    # read in assumed CA
    CA = pd.read_csv(
        "results/" 
        + "CA_" 
        + data_date.strftime("%Y-%m-%d") 
        + ".csv"
    )

    # read in cases by infection dates
    cases = pd.read_csv(
        "results/" 
        + "cases_" 
        + data_date.strftime("%Y-%m-%d") 
        + ".csv",
        parse_dates=["date_inferred"]
    )

    # scale the local cases by the assumed CA 
    cases["local_scaled"] = cases["local"] 
    cases.loc[cases.date_inferred <= pd.to_datetime("2021-12-09"), "local_scaled"] *= 1 / 0.75
    cases.loc[cases.date_inferred > pd.to_datetime("2021-12-09"), "local_scaled"] *= 1 / 0.50

    # read in the inferred susceptibility depletion factor and convert to a simple array
    samples = pd.read_csv(
        "results/"
        + data_date.strftime("%Y-%m-%d") 
        + "/posterior_sample_"
        + data_date.strftime("%Y-%m-%d") 
        + ".csv"
    )
    sus_dep_factor = samples["phi"][:2000]
    sus_dep_factor.to_csv(
        "results/"
        + data_date.strftime("%Y-%m-%d") 
        + "sampled_susceptible_depletion_"
        + data_date.strftime("%Y-%m-%d")
        + ".csv"
    )
    sus_dep_factor = sus_dep_factor.to_numpy()

    states = sorted(["NSW", "QLD", "SA", "VIC", "TAS", "WA", "ACT", "NT"])

    # init a dataframe to hold the Reff samples without susceptible depletion
    df_Reff_adjusted = pd.DataFrame()
    df_cases_adjusted = pd.DataFrame()

    for state in states:
        # filter cases by the state and after March 2020 
        cases_state = cases.loc[cases.STATE == state]
        dates_complete = pd.DataFrame(
            pd.date_range(
                start=df_Reff.INFECTION_DATES.min(), 
                end=max(df_Reff.INFECTION_DATES)
            ), 
            columns=["date_inferred"],
        )
        # merging on date_inferred forces missing dates to be added into cases_state 
        cases_state = dates_complete.merge(right=cases_state, how='left', on='date_inferred')
        cases_state.fillna(0, inplace=True)
        cases_state.loc[cases_state.date_inferred <= "2021-06-25", "local_scaled"] = 0
        cases_state["cum_local_scaled"] = cases_state["local_scaled"].cumsum()
        df_cases_adjusted = pd.concat((df_cases_adjusted, cases_state), axis=0)
        
        cases_state = cases_state.cum_local_scaled.to_numpy()
        cases_state = np.tile(cases_state, (2000, 1)).T
        # invert the susceptible depletion factor for the model
        scaling_factor = 1 / (1 - sus_dep_factor * cases_state / pop_sizes[state])

        df_Reff_state = df_Reff.loc[df_Reff.STATE == state]
        df_Reff_state.iloc[:, :-2] = df_Reff_state.iloc[:, :-2] * scaling_factor
        df_Reff_adjusted = pd.concat((df_Reff_adjusted, df_Reff_state), axis=0)
        

    # save the unscaled Reff
    df_Reff_adjusted.to_csv(
        "results/EpyReff/Reff_"
        + strain
        + "_samples"
        + data_date.strftime("%Y-%m-%d")
        + ".csv",
        index=False,
    )
    
    df_cases_adjusted.to_csv(
        "results/EpyReff/cases_adjusted_"
        + data_date.strftime("%Y-%m-%d")
        + ".csv",
        index=False,
    )
    
    return None 


def remove_sus_with_waning_from_Reff(strain, data_date):
    """
    This removes the inferred susceptibility depletion from the Reff estimates out of EpyReff. 
    The inferred Reff = S(t) * Reff_1 where S(t) is the effect of susceptible depletion (i.e. a 
    factor between 0 and 1) and includes the effects of waning, and Reff_1 is the Reff without 
    the effect of a reducing susceptibility pool.
    """
    from params import pop_sizes

    data_date = pd.to_datetime(data_date)
    # read in Reff samples
    df_Reff = pd.read_csv(
        "results/EpyReff/Reff_" 
        + strain 
        + "_samples" 
        + data_date.strftime("%Y-%m-%d")
        + "tau_4.csv",
        parse_dates=["INFECTION_DATES"],
    )

    # read in cases by infection dates
    cases = pd.read_csv(
        "results/" 
        + "cases_" 
        + data_date.strftime("%Y-%m-%d") 
        + ".csv",
        parse_dates=["date_inferred"]
    )

    # scale the local cases by the assumed CA 
    cases["local_scaled"] = cases["local"] 
    cases.loc[cases.date_inferred <= pd.to_datetime("2021-12-09"), "local_scaled"] *= 1 / 0.75
    cases.loc[cases.date_inferred > pd.to_datetime("2021-12-09"), "local_scaled"] *= 1 / 0.50

    # read in the inferred susceptibility depletion factor and convert to a simple array
    samples = pd.read_csv(
        "results/"
        + data_date.strftime("%Y-%m-%d") 
        + "/posterior_sample_"
        + data_date.strftime("%Y-%m-%d") 
        + ".csv"
    )
    sus_dep_factors = samples[["phi[" + str(i + 1) + "]" for i in range(6)]][:2000]
    
    sus_dep_factors.to_csv(
        "results/" 
        + data_date.strftime("%Y-%m-%d") 
        + "/sampled_susceptible_depletion_"
        + data_date.strftime("%Y-%m-%d")
        + ".csv"
    )
    
    sus_dep_factors = sus_dep_factors.iloc[:,:6].to_numpy()

    states = sorted(["NSW", "QLD", "SA", "VIC", "TAS", "WA", "ACT", "NT"])

    # init a dataframe to hold the Reff samples without susceptible depletion
    df_Reff_adjusted = pd.DataFrame()
    df_cases_adjusted = pd.DataFrame()

    for state in states:
        # filter cases by the state and after March 2020 
        cases_state = cases.loc[cases.STATE == state, :].copy()
        dates_complete = pd.DataFrame(
            pd.date_range(
                start=df_Reff.INFECTION_DATES.min(), 
                end=max(df_Reff.INFECTION_DATES)
            ), 
            columns=["date_inferred"],
        )
        # merging on date_inferred forces missing dates to be added into cases_state 
        cases_state = dates_complete.merge(right=cases_state, how='left', on='date_inferred')
        cases_state.fillna(0, inplace=True)
        cases_state.loc[cases_state.date_inferred <= "2021-06-25", "local_scaled"] = 0
        
        t_horizons = [14, 28, 42, 72, 102, 132]
        # take a rolling sum over each period in t_horizons. This will go up to and including a 
        # a given row and so we subtract the original daily infections to account for that
        for t_horizon in t_horizons:
            cases_state.loc[:, "local_scaled_" + str(t_horizon)] = (
                cases_state.loc[:, "local_scaled"]
                .rolling(t_horizon, min_periods=1)
                .sum()
            )    
        
        # to get cases in (30, 60), (60, 90) etc. we need to subtract the cases in the previous 
        # window. do this by reversing the array and then differencing columns 
        t_horizons.reverse()
        
        for i in range(len(t_horizons) - 1):
            cases_state.loc[:, "local_scaled_" + str(t_horizons[i])] = (
                cases_state.loc[:, "local_scaled_" + str(t_horizons[i])]
                - cases_state.loc[:, "local_scaled_" + str(t_horizons[i + 1])]
            )
        
        df_cases_adjusted = pd.concat((df_cases_adjusted, cases_state), axis=0)
        
        # case arrays are for each period considered 
        cases_state_14 = np.tile(cases_state.local_scaled_14.to_numpy(), (2000, 1)).T
        cases_state_28 = np.tile(cases_state.local_scaled_28.to_numpy(), (2000, 1)).T
        cases_state_42 = np.tile(cases_state.local_scaled_42.to_numpy(), (2000, 1)).T
        cases_state_72 = np.tile(cases_state.local_scaled_72.to_numpy(), (2000, 1)).T
        cases_state_102 = np.tile(cases_state.local_scaled_102.to_numpy(), (2000, 1)).T
        cases_state_132 = np.tile(cases_state.local_scaled_132.to_numpy(), (2000, 1)).T
        
        # invert the susceptible depletion factor for the model
        psi = (
            sus_dep_factors[:, 5] * cases_state_14 / pop_sizes[state] 
            + sus_dep_factors[:, 4] * cases_state_28 / pop_sizes[state]
            + sus_dep_factors[:, 3] * cases_state_42 / pop_sizes[state]
            + sus_dep_factors[:, 2] * cases_state_72 / pop_sizes[state]
            + sus_dep_factors[:, 1] * cases_state_102 / pop_sizes[state]
            + sus_dep_factors[:, 0] * cases_state_132 / pop_sizes[state]
        )
        scaling_factor = 1 / (1 - psi)

        df_Reff_state = df_Reff.loc[df_Reff.STATE == state, :].copy()
        df_Reff_state.iloc[:, :-2] = df_Reff_state.iloc[:, :-2] * scaling_factor
        df_Reff_adjusted = pd.concat((df_Reff_adjusted, df_Reff_state), axis=0)

    # save the unscaled Reff
    df_Reff_adjusted.to_csv(
        "results/EpyReff/Reff_"
        + strain
        + "_samples"
        + data_date.strftime("%Y-%m-%d")
        + ".csv",
        index=False,
    )
    
    df_cases_adjusted.to_csv(
        "results/EpyReff/cases_adjusted_"
        + data_date.strftime("%Y-%m-%d")
        + ".csv",
        index=False,
    )
    
    return None 
