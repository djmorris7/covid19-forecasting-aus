"""
This file is used to run the 
"""

include("simulate_states.jl")

# command line parameters 
const file_date = ARGS[1]
const nsims = parse(Int, ARGS[2])

# states to simulate 
const states_to_run = [
    "NSW",
    "QLD",
    "TAS",
    "VIC",
    "WA",
    "ACT",
    "NT",
]
# const states_to_run = [
#     "NSW",
# ]
# run main 
simulate_all_states(file_date, states_to_run, nsims)