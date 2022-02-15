

include("simulate_states.jl")

# parameters to pass to the main function 
const file_date = ARGS[1]

states = [
    "ACT",
    "NSW",
    "NT",
    "QLD",
    "SA",
    "TAS",
    "VIC",
    "WA",
]

# set seed for consistent plots (NOTE: this is not useful when multithreading 
# enabled as we use separate seeds but the simulation pool should handle that)
rng = Random.Xoshiro(2022)

simulation_start_dates = Dict{String, String}(
    "NSW" => "2021-06-23",
    "QLD" => "2021-11-01",
    "SA" => "2021-11-01",
    "TAS" => "2021-11-01",
    "WA" => "2021-12-15",
    "ACT" => "2021-08-01",
    "NT" => "2021-12-01",
    "VIC" => "2021-08-01",
)

# date we want to apply increase in cases due to Omicron 
omicron_dominant_date = Dates.Date("2021-12-15")

# get the latest onset date
latest_start_date = Dates.Date(maximum(v for v in values(simulation_start_dates)))

pop_sizes = Dict{String, Int}(
    "NSW" => 8189266,
    "QLD" => 5221170,
    "SA" => 1773243,
    "TAS" => 541479,
    "VIC" => 6649159,
    "WA" => 2681633,
    "ACT" => 432266,
    "NT" => 246338,
)
    
initial_conditions = Dict{
    String, NamedTuple{(:S, :A, :I), Tuple{Int64, Int64, Int64}}
}(
    "NSW" => (S = 5, A = 8, I = 0),
    "QLD" => (S = 0, A = 0, I = 0),
    "SA" => (S = 0, A = 0, I = 0),
    "TAS" => (S = 0, A = 0, I = 0),
    "VIC" => (S = 20, A = 20, I = 0),
    "WA" => (S = 3, A = 2, I = 0),
    "ACT" => (S = 0, A = 0, I = 0),
    "NT" => (S = 3, A = 2, I = 0),   
)

(local_case_dict, import_case_dict) = read_in_cases(file_date, rng)
dates = local_case_dict["date"]
last_date_in_data = dates[end]
forecast_end_date = last_date_in_data + Dates.Day(35)

# create vector for dates 
onset_dates = latest_start_date:Dates.Day(1):forecast_end_date

# add a small truncation to the simulations as we don't trust the most recent data 
truncation_days = 5

# merge all the simulation and TP files for states into single CSV
merge_simulation_files(file_date)    
merge_TP_files(file_date)
plot_all_forecast_intervals(file_date, states, local_case_dict)