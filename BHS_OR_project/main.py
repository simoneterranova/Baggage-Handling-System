import math 
import pandas as pd
import time
import numpy as np  # added to manage NaN
from instance import *
from solver import *

# This exclude "FutureWarning: The behavior of DataFrame concatenation with 
# empty or all-NA entries is deprecated. In a future version, this will no 
# longer exclude empty or all-NA columns when determining the result dtypes. 
# To retain the old behavior, exclude the relevant entries before the 
# concat operation results = pd.concat([results, pd.DataFrame([formatted_data], 
# columns=columns)], ignore_index=True)". It is showed in the terminal 
# during the code execution.

import warnings
warnings.filterwarnings("ignore", category=FutureWarning) 


# Parameters
num_sources = 4 # 4
num_destinations = 4 #4
num_intermediates = 6 #6
min_c = 100 #100
max_c = 500 #500 
min_c_range = range(min_c, max_c, min_c) #min_c
min_b = 400 #400
max_b = 800 #800
seed = 22 # 22

# tabel result initialization --------------------------------------------------

columns = ['Method', 'Seed', 'Min_Bag', 'Max_Bag', 'Min_c', 'Max_c', 'OF [KWh]', 'Sol_Time [s]', 'Build_Time [s]']
results = pd.DataFrame(columns=columns)

def add_to_results(method, seed, min_b, max_b, min_c, max_c, of, sol_time, build_time):
    global results
    formatted_data = [
        method,
        seed,
        min_b,
        max_b,
        min_c,
        max_c,
        round(of, 2) if isinstance(of, (float, int)) else 'INF',  # Usa NaN per i valori mancanti
        round(sol_time, 2) if sol_time is not None else np.nan,
        round(build_time, 2) if build_time is not None else np.nan
    ]
    results = pd.concat([results, pd.DataFrame([formatted_data], columns=columns)], ignore_index=True)

# ------------------------------------------------------------------------------

# Lists to save the solutions in order to compute the optimality gap
of_method_1 = []
of_method_2 = []
optimality_values = []

#-------------------------------------------------------------------------------

# METHOD 1

for min_c in min_c_range:
    
    built_time_start = time.time()
    G, sources, intermediates, destinations = create_tripartite_graph_nodes(num_sources=num_sources, num_destinations=num_destinations, num_intermediates=num_intermediates, seed=seed, min_baggage=min_b, max_baggage=max_b)
    graph, edges_list = generate_edges(G, sources, intermediates, destinations, seed=seed, min_c=min_c, max_c=max_c)
    built_time_stop = time.time()

    sim_time_start1 = time.time()
    baggage_path = min_cost_computation(G, edges_list)
    sim_time_stop1 = time.time()

    sim_time1 = sim_time_stop1 - sim_time_start1
    built_time = built_time_stop - built_time_start

    total_baggage_consumption = 0

    # given baggage_path, the of value is computed summing all the 
    # baggage consumption associated to thei paths.

    if baggage_path:
        for bag_id, bag_info in baggage_path.items():
            single_baggage_consumption = bag_info[1][2] + bag_info[2][2]
            total_baggage_consumption += single_baggage_consumption
        of = total_baggage_consumption
    else:
        of = np.nan  # Nan if the OF is infeasible

    of_method_1.append(of) # The solution is saved
    
    # Add the solution to the table
    add_to_results('Method 1', seed, min_b, max_b, min_c, max_c, of, sim_time1, built_time)

# ------------------------------------------------------------------------------

# METHOD 2

# enumerate is needed since (i,capacity) structure is useful to exploit
# the index 'i' to compute the optimality gap at the end of each for iteration

for min_c_index, min_c in enumerate(min_c_range):

    built_time_start = time.time()
    G, sources, intermediates, destinations = create_tripartite_graph_nodes(num_sources=num_sources, num_destinations=num_destinations, num_intermediates=num_intermediates, seed=seed, min_baggage=min_b, max_baggage=max_b)
    graph, edges_list = generate_edges(G, sources, intermediates, destinations, seed=seed, min_c=min_c, max_c=max_c,)
    built_time_stop = time.time()

    sim_time_start2 = time.time()
    baggage_path, of = local_search_with_neighborhood(G, edges_list, max_iterations=100)
    sim_time_stop2 = time.time()

    sim_time2 = sim_time_stop2 - sim_time_start2
    built_time = built_time_stop - built_time_start

    of_method_2.append(of) # save the solution

    # Optimality gap computation between method 1 and method 2 solutions
    # related to the same iteration.

    of1 = of_method_1[min_c_index] # here is where the enumerate helps

    if isinstance(of1, (float, int)) and isinstance(of, (float, int)):
        # Feasible solution
        optm_gap = abs(of1 - of) / of * 100
        optimality_values.append(optm_gap)

    else:
        # Infeasible solution
        optm_gap = None
        optimality_values.append(optm_gap)

    # Addition of the solution to the table
    add_to_results('Method 2', seed, min_b, max_b, min_c, max_c, of, sim_time2, built_time)

# results show
print("\n")
print(results)
print("\n")
print("Optimality Gap percentage between Method1 and Method2 for each iteration:\n")

# Optimality gap show

i = 1
for value in optimality_values:
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            print(f"{i}: {value}")
        else:
            print(f"{i}: {value:.2f} %")
    else:
        print(f"{i}: {value}")
    i += 1
print("\n")

