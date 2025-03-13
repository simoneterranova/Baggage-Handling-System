import networkx as nx
import matplotlib.pyplot as plt
import random
from networkx.algorithms.flow import min_cost_flow
from .instance_gen import *

def create_tripartite_graph_nodes(num_sources=2, num_destinations=2, 
    num_intermediates=3, seed = None, min_baggage = 10, max_baggage = 30, 
    min_b_weight = 10, max_b_weight = 25):
    
    """This function exploits the networkx framework to build the graph nodes, 
        having as input parameters the number of inputs,intermediates and output
        nodes and data related to baggage. More in detail, upper and lower
        bounds are specified for baggage amount and their weights"""
    
    # Step 1: fix the seed and verify that the number of input nodes is equal 
    # to the destinations

    random.seed(seed)
    if num_sources != num_destinations:
        raise ValueError("The number of sources must equal the number of" 
                         "destinations for one-to-one matching.")
    
    # Step 2: Create the Graph

    G = nx.DiGraph()

    # Step 3: define nodes for the bipartite graph

    # Source nodes (S1, S2, ...)
    sources = [f'S{i+1}' for i in range(num_sources)]  
    # Intermediate nodes (I1, I2, ...)
    intermediates = [f'I{i+1}' for i in range(num_intermediates)]
    # Destination nodes (D1, D2, ...)
    destinations = [f'D{i+1}' for i in range(num_destinations)]  

    # Step 4: Add nodes

    G.add_nodes_from(sources + intermediates + destinations)

    # Step 5: Define the supply at sources and corresponding demand 
    # at destinations

    bag_id_index = 1 # index used to assign a unique identifier to each baggage

    for i in range(num_sources):

        # Random supply between min and max baggage
        supply = random.randint(min_baggage,max_baggage)  
        
        # G.nodes is a NodeView object. Specifying the node name following 
        # the sintax G.nodes['node_name'] you can access the node attributes. 
        # In this case there are 'demand' related to the number of baggages 
        # generated or collected by that node, and 'baggage_list' that is a 
        # dictionary where the key is a generic index j and the value is a 
        # Baggage class instance

        # Store supply as negative demand
        G.nodes[f'S{i+1}']['demand'] = -supply
        
        # initialize the data structure to collect all the info about baggage
        # stored in the node
        G.nodes[f'S{i+1}']['baggage_list'] = {} 

        # Once the node structure is defined, all the baggages are created and 
        # added to the baggage_list

        # it starts from 0 since the upper bound is exclusive
        for j in range(0,supply): 
            
            # a baggage is a Baggage class instance, so we need to define
            # its attributes (weight,destination, start, id)
            baggage_weight = random.randint(min_b_weight,max_b_weight)
            baggage_destination = f'D{i+1}'
            baggage_start = f'S{i+1}'
            baggage_id = bag_id_index
            baggage = Baggage(baggage_weight,baggage_start, baggage_destination,
                               baggage_id)
            bag_id_index += 1
            
            G.nodes[f'S{i+1}']['baggage_list'][j+1] = baggage
        
        # For destination and intermediate nodes, empty sets are created to be
        # filled during the heuristic algorithm.
        # Matching demand at the corresponding destination:
        G.nodes[f'D{i+1}']['demand'] = supply
        G.nodes[f'D{i+1}']['baggage_list'] = {}

    # Step 6: set demand for intermediate nodes to zero

    for i in intermediates:

        G.nodes[i]['demand'] = 0
        G.nodes[i]['baggage_list'] = {}

        # The following parameters are used in MCF_heu.py for the security check

        # these parameters associated only to intermediate nodes, report the
        # capacity and weight values of the links connecting 'i' to each
        # destination nodes with the sintax {'destination name': weight/capacity}
        G.nodes[i]["output_edge_capacity"] = {}
        G.nodes[i]["output_edge_weight"] = {}

        # these parameters have the same structure of the previous two but they
        # are related to the total amount of weight and capacity used by those
        # baggage that have already been sent to that given output link.
        G.nodes[i]["current_edge_weight"] = {}
        G.nodes[i]["current_edge_capacity"] = {}
        
        for d in destinations:
            # destination values initialization
            G.nodes[i]["current_edge_weight"][d] = 0
            G.nodes[i]["current_edge_capacity"][d] = 0      
        
      

    return G, sources, intermediates, destinations


def generate_edges(graph, sources, intermediates, destinations, 
    seed = None, min_c = 10, max_c = 20, 
    min_power = 1, max_power = 10 ):
   
    """This function aims to create graph edges with random capacities, wieghts
        and power coefficient. It receives as inputs the previous generated
        graph 'graph', the lists of nodes, and upper and lower
        bounds values for weight, capacity and power of the edge """

    # Step 1: fix the seed and initialize edge_list. It is a dictionary
    # { 'key': 'edge x to y', value: {'info': conveyor_belt instance} }.
    # This disctionary is used to report all the edge info and to manage
    # them in an easier way. Morover, also the conveyor belt id (id_index) 
    # is initialized

    random.seed(seed)
    edges_list = {}
    id_index = 1

    # Step 2: Generate edges from source to intermediate nodes

    for s in sources:

        for i in intermediates:

            # Random capacity
            max_capacity = random.randint(min_c,max_c)

            # Random weight related to the capacity. More capacity means
            # more supported weight. Lower and upper bounds are choosen 
            # as the product between the min capacity of the edge times
            # the average weight of a baggage, and the max capacity of the edge
            # times the maximum baggage weight.

            max_weight = random.uniform(max_capacity*((25+10)/2), max_capacity*((25+10)/2) ) 
            
            # power coefficient
            kp = random.uniform(0.00001*max_capacity*min_power,
                                0.00001*max_capacity*max_power) 
            
            # Conveyor belt index
            id = id_index 
            id_index += 1
            
            # The edge is added to the graph through networkx function
            graph.add_edge(s, i, capacity = max_capacity , weight = max_weight, 
                           power = kp, id=id)
            
            # An equivalent edge object instance is created. It is easier to 
            # be managed for next computations with respect to the graph 
            # edge data
            edge = Conveyor_belt(max_capacity,max_weight, kp, i, s, id)
            
            info = {}
            info["info"] = edge
            edges_list[f"edge {s} to {i}"] = info

    # Step 3: Generate edges form Intermediate to Destination nodes
    for i in intermediates:

        for d in destinations:
            
            # Generate a random capacity for the edge, respecting the 
            # intermediate node's capacity
            max_capacity = random.randint(min_c, max_c)
            max_weight = random.uniform(max_capacity*((25+10)/2), max_capacity*((25+10)/2) )
            kp = random.uniform(0.00001*max_capacity*min_power,
                                0.00001*max_capacity*max_power)
            id = id_index
            id_index += 1
            
            graph.add_edge(i, d, capacity = max_capacity, weight = max_weight, 
                           power = kp, id = id)
            edge = Conveyor_belt(max_capacity,max_weight, kp, d, i, id)
            
            info = {}
            info["info"] = edge
            edges_list[f"edge {i} to {d}"] = info

            graph.nodes[i]["output_edge_capacity"][d] = max_capacity
            graph.nodes[i]["output_edge_weight"][d] = max_weight


    #plot_graph(len(intermediates), len(destinations), sources, intermediates, destinations, graph)

    return graph, edges_list
                

def plot_graph(num_intermediates, num_destinations, sources, intermediates, 
               destinations, G):
    
    """Graph plot generation function"""

    # Set positions for sources
    pos = {node: (0, i) for i, node in enumerate(sources + 
                                                 intermediates + destinations)}

    # Set positions for intermediates, distribute them along the y-axis
    pos.update({f'I{i+1}': (1, i) for i in range(num_intermediates)})

    # Set positions for destinations
    pos.update({f'D{i+1}': (2, i) for i in range(num_destinations)})

    # Draw the graph
    plt.figure(figsize=(12, 8))  # Increased size for better readability
    nx.draw(G, pos, with_labels=False, node_color='lightblue', edge_color='gray',
            node_size=2000, font_size=7)

    # Draw edge capacities and weights, adjusting positions
    edge_labels = {(u, v): f'C: {attr["capacity"]}, W: {int(attr["weight"])}'
                   for u, v, attr in G.edges(data=True)}

    # Set font size for edge labels
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, label_pos=0.2, 
                                 font_size=7)  # Reduced font size

    # Annotate nodes with supply/demand and intermediate flows
    node_labels = {
        node: (f'{node}\n(Supply: {-data.get("demand", 0)})' if data.get("demand", 0) < 0 
               else f'{node}\n(Demand: {data.get("demand", 0)})')
        for node, data in G.nodes(data=True)
    }

    # Draw node labels
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=7, 
                            verticalalignment='center')

    plt.show()



