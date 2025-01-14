"""
Author: Dylan Morris
Date: 10 Feb 2022 at 6:15:09 pm
Description: 
Use this script to quickly plot diagnostics of a chain. This could involve scatter-plots 
to assess correlations between parameters, traceplots to check for divergent behaviours and
also just assessing the overall reasonableness of the posterior samples. 
"""

let
    # for dataframe handling 
    using DataFrames
    using CSV
    using Chain

    # nice plotting 
    using StatsPlots
    using PlotThemes
    using Plots
    using LaTeXStrings

    # analysis/commonly used
    using Statistics
    using StatsBase 
    using Dates
    using KernelDensity
    using Random
    using Distributions
    using BenchmarkTools
    using ProgressBars
end

gr()

default(
	linewidth=1.5, 
	label=nothing, 
	framestyle=:box,
)
scalefontsizes(0.95)

##

samples = CSV.read(
    "results/2022-04-05/posterior_sample_2022-04-05.csv", 
    DataFrame, 
)

par = "phi[1]"
par = "prop_md_third[391]"
par = "prop_md_third[391]"


num_samples = nrow(samples)
num_chains = 4
m = num_samples ÷ num_chains

par = "mu_hat_third[392]"
par = "md_third[392]"
par = "theta_md"

fig = plot(layout = (2, 1))
for i in 1:4
    idx = 1 + m * (i - 1):m * i
    plot!(fig, subplot = 1, samples[idx, par])
    plot!(fig, subplot = 2, kde(samples[idx, par]))
end
display(fig)

plot(samples[1:1000,par])
plot!(samples[1001:2000,par])
plot!(samples[2001:3000,par])
plot!(samples[3001:4000,par])

plot(kde(samples[1:1000,par]))
plot!(kde(samples[1001:2000,par]))
plot!(kde(samples[2001:3000,par]))
plot!(kde(samples[3001:4000,par]))

scatter(samples[!, "m1[7]"], samples[!, "r[7]"])

x = [samples[!, "phi[" * string(i) * "]"] for i in range(1, 4)]


fig = plot(layout = 12, legend = false)
for i in 369:380
    plot!(fig, subplot = i - 368, samples[!, "prop_md_third_wave." * string(i)])
end
fig

fig = plot(layout = 12, legend = false)
for i in 369:380
    plot!(fig, subplot = i - 368, kde(samples[!, "prop_md_third_wave." * string(i)]))
end
fig

plot(samples[1:1000, "prop_md_third_wave.370"])
plot!(samples[1001:2000, "prop_md_third_wave.370"])
plot!(samples[2001:3000, "prop_md_third_wave.370"])
plot!(samples[3001:4000, "prop_md_third_wave.370"])

plot(kde(samples[1:1000, "prop_md_third_wave.370"]))
plot!(kde(samples[1001:2000, "prop_md_third_wave.370"]))
plot!(kde(samples[2001:3000, "prop_md_third_wave.370"]))
plot!(kde(samples[3001:4000, "prop_md_third_wave.370"]))

plot(samples[1:1000, "bet.5"])
plot!(samples[1001:2000, "bet.5"])
plot!(samples[2001:3000, "bet.5"])
plot!(samples[3001:4000, "bet.5"])

plot((cumsum(samples[1:1000, "bet.5"])) ./ (1:1000))
plot!((cumsum(samples[1001:2000, "bet.5"])) ./ (1:1000))
plot!((cumsum(samples[2001:3000, "bet.5"])) ./ (1:1000))
plot!((cumsum(samples[3001:4000, "bet.5"])) ./ (1:1000))

plot(kde(samples[1:1000, "bet.4"]))

plot!(kde(samples[1001:2000, "bet.4"]))
plot!(kde(samples[2001:3000, "bet.4"]))
plot!(kde(samples[3001:4000, "bet.4"]))

plot(samples[!, "theta_md"])
plot(samples[1:2000, "theta_md"])
plot!(samples[2001:4000, "theta_md"])
plot!(samples[4001:6000, "theta_md"])
plot!(samples[6001:8000, "theta_md"])

plot(kde(samples[!, "theta_md"]))

# scatter(samples[!, "tau.8"], samples[!, "r.8"])
# xlabel!("days after 15/11/2021")
# ylabel!("rate of increase for the sigmoid")

# f(x, m0, m1, r, tau) = m0 + (m1 - m0) / (1 + exp(-r * (x - tau)))
# (m01, m11, r1, tau1) = (0.05, 0.95, 0.025, 25)
# f1(x) = f(x, m01, m11, r1, tau1)
# (m02, m12, r2, tau2) = (0.05, 0.95, 0.6, 17)
# f2(x) = f(x, m02, m12, r2, tau2)

# plot(0:50, f1.(0:50))
# plot!(0:50, f2.(0:50))

using MCMCDiagnostics

function ess(X)

    # get number of samples and parameters
    (samp, par) = size(X)

    # vector for storing ESS 
    n_eff = zeros(par)

    # lags to evaluate the correlations at
    lags = convert.(Int, round.(0:ceil(samp / 2), digits = 0))

    # now evaluate ess for each parameter
    for ii = 1:par 
        ac1 = autocor(X[:,ii], lags)
        cut = findfirst(x -> x < 0, ac1)
        pt_total = sum(ac1[2:cut])
        n_eff[ii] = samp / (1 + 2 * pt_total)
    end

    return n_eff

end


cut = findfirst(x -> x < 0, ac1)
pt_total = sum(ac1[2:cut])
n_eff[ii] = samp / (1 + 2 * pt_total)

samples_only = samples[1:1000, 9:end]
samples_mat = Matrix(samples_only)

# get number of samples and parameters
(samp, par) = size(samples_mat)

# vector for storing ESS 
n_eff = zeros(par)

# lags to evaluate the correlations at
lags = convert.(Int, round.(0:ceil(samp / 2), digits = 0))

# now evaluate ess for each parameter
ii = 5
ac1 = autocor(samples_mat[:,ii], lags)
plot(ac1[1:10])

ess_samples_only = ess(samples_mat)
# some negative ess???
bad_samples = findall(ess_samples_only .< 0)

plot(samples_mat[:, bad_samples[1:5]], layout = 5)

samples_only[!,9136:9138]

plot_kde = true
plot_traceplots = false

# filter by divergent samples
# samples_good = filter(:divergent__ => ==(0.0), samples)
# samples_divergent = filter(:divergent__ => ==(1.0), samples)

# plot traceplots for ALL parameters in samples (this will take a few minutes and 
# will produce quite a large pdf).
samples = CSV.read(
    "results/2022-03-22/50_case_ascertainment/posterior_sample_2022-03-22.csv", 
    DataFrame, 
)

let

    num_samples = nrow(samples)
    num_each_chain = num_samples ÷ 4
    
    sp = 1
    page = 1

    names_to_plot = names(samples)

    fig = plot(
        layout = (8,5),
        dpi=200, 
        size=(1000,1200), 
        # link=:x, 
        framestyle=:minimal, 
        legend = false,
    )

    for name in ProgressBar(names_to_plot)
        if sp == 1
            fig = plot(
                layout = (8,5),
                dpi=200, 
                size=(1000,1200), 
                # link=:x, 
                framestyle=:minimal, 
                legend = false,
            )
        end
        # plot!(fig, subplot = sp, samples[!,name])
        for i in 1:4
            plot!(fig, subplot = sp, kde(samples[(1 + (i - 1) * num_each_chain):(i * num_each_chain),name]))
        end
        xlabel!(fig, subplot = sp, name)
        sp += 1
        if sp == 8*5 + 1 || sp == length(names_to_plot) + 1
            sp = 1 
            savefig(fig, "tmp_plots/page"*string(page)*".pdf")
            page += 1
        end
    end

    using PDFmerger

    pdf_filenames = [
        "tmp_plots/page"*string(p)*".pdf" for p in 1:page-1
    ]

    merge_pdfs(
        pdf_filenames, 
        "tmp_plots/kde.pdf",
        cleanup=true,
    )

    sp = 1
    page = 1

    names_to_plot = names(samples)

    fig = plot(
        layout = (8,5),
        dpi=200, 
        size=(1000,1200), 
        # link=:x, 
        framestyle=:minimal, 
        legend = false,
    )

    for name in ProgressBar(names_to_plot)
        if sp == 1
            fig = plot(
                layout = (8,5),
                dpi=200, 
                size=(1000,1200), 
                # link=:x, 
                framestyle=:minimal, 
                legend = false,
            )
        end
        # plot!(fig, subplot = sp, samples[!,name])
        for i in 1:4
            plot!(fig, subplot = sp, samples[(1 + (i - 1) * num_each_chain):(i * num_each_chain),name])
        end
        xlabel!(fig, subplot = sp, name)
        sp += 1
        if sp == 8*5 + 1 || sp == length(names_to_plot) + 1
            sp = 1 
            savefig(fig, "tmp_plots/page"*string(page)*".pdf")
            page += 1
        end
    end

    using PDFmerger

    pdf_filenames = [
        "tmp_plots/page"*string(p)*".pdf" for p in 1:page-1
    ]

    merge_pdfs(
        pdf_filenames, 
        "tmp_plots/traceplots.pdf",
        cleanup=true,
    )
    
end

#########################

# Code for assessing the fitted TP (μ(t)) coming out of stan against the forecasted 
# estimates. More of a sanity check than anything else and just helps to see that the
# posterior sampled μ(t) and recombined/forecasted estimates align. 

state = "TAS"

# mu_hat_filtered_old = CSV.read(
#     "results/UoA_forecast_output/2022-02-15/" * state * "_2022-02-15_TP.csv",
#     DataFrame,
# )

mu_hat_local = CSV.read(
    "mu_hat_Australian Capital Territory.csv", 
    DataFrame, 
    drop = [1],
)

mu_hat_all = CSV.read(
    "results/soc_mob_R2022-02-22.csv", 
    DataFrame,
    drop = [1],
)

mu_hat_forecast = @chain mu_hat_all begin 
    subset(
        :type => ByRow(==("R_L")), 
        :state => ByRow(==(state)),
    )
end

mu_hat_filtered = CSV.read(
    "results/UoA_forecast_output/2022-02-22/" * state * "_2022-02-22_TP.csv",
    DataFrame,
)

Reff_delta = CSV.read(
    "results/EpyReff/Reff_delta2022-03-08tau_5.csv", 
    DataFrame
)
Reff_omicron = CSV.read(
    "results/EpyReff/Reff_omicron2022-03-08tau_5.csv", 
    DataFrame
)

fig = plot(layout = (4, 2), size = (800, 800)) 
plot!(fig, Reff_delta.INFECTION_DATES, Reff_delta.mean, group = Reff_delta.STATE, lc = 1)
plot!(fig, Reff_delta.INFECTION_DATES, Reff_delta.bottom, group = Reff_delta.STATE, lc = 1, ls = :dash)
plot!(fig, Reff_delta.INFECTION_DATES, Reff_delta.top, group = Reff_delta.STATE, lc = 1, ls = :dash)
plot!(fig, Reff_omicron.INFECTION_DATES, Reff_omicron.mean, group = Reff_omicron.STATE, lc = 2)
plot!(fig, Reff_omicron.INFECTION_DATES, Reff_omicron.bottom, group = Reff_omicron.STATE, lc = 2, ls = :dash)
plot!(fig, Reff_omicron.INFECTION_DATES, Reff_omicron.top, group = Reff_omicron.STATE, lc = 2, ls = :dash)
xlims!((Dates.Date("2021-12-01"), Dates.Date("2022-03-05")))
ylims!(0.5, 3)

Reff_delta = filter(:STATE => ==("NSW"), Reff_delta)
Reff_omicron = filter(:STATE => ==("NSW"), Reff_omicron)

fig = plot(size = (800, 800)) 
plot!(fig, Reff_delta.INFECTION_DATES, Reff_delta.mean, lc = 1)
plot!(fig, Reff_delta.INFECTION_DATES, Reff_delta.bottom, lc = 1, ls = :dash)
plot!(fig, Reff_delta.INFECTION_DATES, Reff_delta.top, lc = 1, ls = :dash)
plot!(fig, Reff_omicron.INFECTION_DATES, Reff_omicron.mean, lc = 2)
plot!(fig, Reff_omicron.INFECTION_DATES, Reff_omicron.bottom, lc = 2, ls = :dash)
plot!(fig, Reff_omicron.INFECTION_DATES, Reff_omicron.top, lc = 2, ls = :dash)
vline!(fig, [Dates.Date("2021-12-13")], lc = :black, ls = :dash, lw = 2)
vline!(fig, [Dates.Date("2021-11-15")], lc = :green, ls = :dash, lw = 2)
xlims!((Dates.Date("2021-11-10"), Dates.Date("2022-03-05")))
ylims!(0.5, 1.7)

Reff_state = filter(:STATE => ==(state), Reff)
plot(
    mu_hat_forecast.date, 
    mean(Matrix(mu_hat_forecast[!,9:end]), dims = 2),
    label = "mu"
)
mu_hat_filtered_median = median(Matrix(mu_hat_filtered[:,3:end-1]), dims = 2)
plot!(
    mu_hat_filtered[:,"onset date"], 
    mu_hat_filtered_median,    
    label = "filtered mu"
)
mu_hat_local_median = median(Matrix(mu_hat_local[:,3:end-1]), dims = 1)[:]
t0 = Dates.Date("2021-12-01")
Δt = Dates.Day(1)
t1 = t0 + Dates.Day(length(mu_hat_local_median)-1)
dr = t0:Δt:t1
plot!(
    dr, 
    mu_hat_local_median,    
    label = "fitted mu"
)
plot!(
    Reff_state[:,"INFECTION_DATES"], 
    Reff_state[:,"median"],    
    label = "Reff"
)
vline!(
    [Dates.Date("2021-12-19")]
)
ylims!((0,2))
# xlims!((NSW_date_range[1], NSW_date_range[end] + Dates.Day(35)))
xlims!((Dates.Date("2021-12-15"), Dates.Date("2021-12-15") + Dates.Day(60)))

Reff_state = filter(:STATE => ==(state), Reff)
plot(
    mu_hat_forecast.date, 
    Matrix(mu_hat_forecast[!,9:end]),
    label = "mu", 
    lc = 1, 
    leg = false, 
)
# mu_hat_filtered_median = median(Matrix(mu_hat_filtered[:,3:end-1]), dims = 2)
# plot!(
#     mu_hat_filtered[:,"onset date"], 
#     mu_hat_filtered_median,    
#     label = "filtered mu"
# )
mu_hat_local_mat = Matrix(mu_hat_local[:,3:end-1])'
t0 = Dates.Date("2021-12-01")
Δt = Dates.Day(1)
t1 = t0 + Dates.Day(length(mu_hat_local_median)-1)
dr = t0:Δt:t1
plot!(
    dr, 
    mu_hat_local_mat,    
    lc = 2, 
)
vline!(
    [Dates.Date("2021-12-19")]
)
ylims!((0,2))
# xlims!((NSW_date_range[1], NSW_date_range[end] + Dates.Day(35)))
xlims!((Dates.Date("2021-12-15"), Dates.Date("2021-12-15") + Dates.Day(60)))

mu_hat_VIC = CSV.read(
    "./mu_hat_VIC.csv", 
    DataFrame,
    drop = [1],
)

mu_hat_all = CSV.read(
    "results/soc_mob_R2022-02-01.csv", 
    DataFrame,
    drop = [1],
)

mu_hat_VIC_filtered = CSV.read(
    "results/UoA_forecast_output/2022-02-09/VIC_2022-02-09_TP.csv",
    DataFrame,
)

mu_hat_VIC_forecast = @chain mu_hat_all begin 
    subset(
        :type => ByRow(==("R_L")), 
        :state => ByRow(==("VIC")),
    )
end

VIC_date_range = Dates.Date("2021-08-15"):Dates.Day(1):Dates.Date("2021-06-15")+Dates.Day(nrow(mu_hat_VIC)-1)
plot(
    VIC_date_range, 
    median(Matrix(mu_hat_VIC), dims = 2),
)
plot!(
    mu_hat_VIC_forecast.date, 
    mu_hat_VIC_forecast.median,
)

mu_hat_VIC_filtered_median = median(Matrix(mu_hat_VIC_filtered[:,3:end-1]), dims = 2)
plot!(
    mu_hat_VIC_filtered[:,"onset date"], 
    mu_hat_VIC_filtered_median,    
)
xlims!((VIC_date_range[1], VIC_date_range[end]))

# pars = [
#     "bet.1",
#     "bet.2",
#     "bet.3",
#     "bet.4",
#     "bet.5",
#     "theta_masks", 
#     "voc_effect_delta", 
#     "voc_effect_omicron",
#     "susceptible_depletion_factor", 
# ]

# sp = 1
# page = 1

# fig = plot(
#     layout = 9,
#     dpi=200, 
#     size=(1000,1000), 
#     framestyle=:minimal, 
#     legend = false,
# )

# for x in ProgressBar(pars)
#     for y in pars
#         if sp == 1
#             fig = plot(
#                 layout = 9,
#                 dpi=200, 
#                 size=(1000,1000), 
#                 framestyle=:minimal, 
#                 legend = false,
#             )
#         end
#         scatter!(
#             fig, subplot = sp, samples[:,x], samples[:,y]
#         )
#         xlabel!(fig, subplot = sp, x)
#         ylabel!(fig, subplot = sp, y)
#         sp += 1
#     end
#     sp = 1 
#     savefig(fig, "tmp_plots/page"*string(page)*".pdf")
#     page += 1
# end

# pdf_filenames = [
#     "tmp_plots/page"*string(p)*".pdf" for p in 1:page-1
# ]

# merge_pdfs(
#     pdf_filenames, 
#     cleanup=true,
# )

# f = plot(layout = 2)
# scatter!(f, subplot = 1, samples[:,"voc_effect_delta"], samples[:, "theta_md"])
# xlabel!(f, subplot = 1, "voc_effect_delta")
# ylabel!(f, subplot = 1, "theta_md")
# scatter!(f, subplot = 2, samples[:,"voc_effect_omicron"], samples[:, "theta_md"])
# xlabel!(f, subplot = 2, "voc_effect_omicron")
# ylabel!(f, subplot = 2, "theta_md")
# savefig(f, "correlations.pdf")

mu_hat_filtered_old = CSV.read(
    "results/UoA_forecast_output/2022-02-02/NT_2022-02-02_TP.csv",
    DataFrame,
)

mu_hat_filtered = CSV.read(
    "results/UoA_forecast_output/2022-02-09/NSW_2022-02-09_TP.csv",
    DataFrame,
)

# nice hack for datetime range
start_date = Dates.Date("2021-06-15")
Δt = Dates.Day(1)
end_date = start_date + Dates.Day(nrow(mu_hat)-1)
date_range = start_date:Δt:end_date

mu_hat_filtered_old_median = median(Matrix(mu_hat_filtered_old[:,3:end-1]), dims = 2)
mu_hat_filtered_median = median(Matrix(mu_hat_filtered[:,3:end-1]), dims = 2)
plot(
    mu_hat_filtered_old[:,"onset date"], 
    mu_hat_filtered_old_median,    
)
plot!(
    mu_hat_filtered[:,"onset date"], 
    mu_hat_filtered_median,    
)
# xlims!((NSW_date_range[1], NSW_date_range[end] + Dates.Day(35)))

D = rand(100, 3, 1000)
case_counts = zeros(100)
case_counts1 = zeros(100)
@btime $case_counts1 .= sum(@view($D[:, 1:2, 1]), dims = 2)

function count_cases!(case_counts, D, sim)
    
    for i in 1:length(case_counts)
        case_counts[i] = D[i,1,sim] + D[i,2,sim]
    end
    
    return nothing
end

@btime count_cases!($case_counts, $D, 1)