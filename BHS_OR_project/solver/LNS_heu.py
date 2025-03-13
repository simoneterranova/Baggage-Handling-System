from instance.instance_gen import *
import copy
import random

def first_feasible_solution_generator(G,edges):

    """
    This function aims to find a feasible solution that is not necessary
    the optimal one. Indeed, it is used as starting solution to be improved
    with the local search algorithm. It takes as inputs the graph and the 
    edges info, and it returns "first_baggage_path_guess" that is a dictionary
    with structure {'baggage_id':["starting node", baggage instance,('next node', 
    conveyor belt used to reach the next node, single baggage consumption)] }, 
    that is equivalent to the "baggage_best_path" of 'heurstic.py' with the 
    addition of the baggage instance that has a specific use in the code.
    
    """

    # organization of the nodes list. Even if nodes information are 
    # already associated to the graph structure, it is useful to define 
    # three different lists for input, intermediate and output nodes. This 
    # is done to manage nodes information in an easier way, making also
    # the code more readable.

    s = 0
    i = 0
    d = 0
    
    input = []
    intermediate = []
    output = []
    
    # "data = True" is specified according to take node data during the for loop.
    # Without this specification, "node" would be just a string with the node name
    # On the other hand, with this instruction, node is a tuple structure
    # ("node name", {"demand": x, "baggage_list": {} }).

    for node in G.nodes(data = True):
        if node[0] == f'S{s+1}':
            input.append(node)
            s += 1
        if node[0] == f'I{i+1}':
            intermediate.append(node)
            i += 1
        if node[0] == f'D{d+1}':
            output.append(node)
            d += 1
     
    # dictionary filled up as explained at the beginnin of the function. Here
    # it is reported again its sintax {'baggage_id':["starting node", 
    # baggage instance,('next node', 
    # conveyor belt used to reach the next node, single baggage consumption)] }

    first_baggage_path_guess = {}

    j = 1  # baggage index in the baggage list of the graph nodes

    # total amount of intermediate nodes, tht is exploted in the next for
    int_node = len(intermediate) 

    # node is ('node_name', {'demand: , 'baggage_list': {} } )
    for node in input: 
        
        i = 1 # intermediate node index

        # for each input node, we scan all its baggage one by one
        for b in range(1,len(node[1]['baggage_list'])+1):
            
            # we take the information related to the baggage still stored
            # in the input node buffer

            bag = node[1]['baggage_list'][b]
            bag_w = bag.weight
            bag_d = bag.destination
            bag_s = bag.start

            # the path of the first guess is initialized here for that given
            # baggage in this for loop

            first_baggage_path_guess[bag.id] = []
            first_baggage_path_guess[bag.id].append(bag_s) # baggage source
            first_baggage_path_guess[bag.id].append(bag) # bag instance

            check_c = False # constraints check
            check_F = False # feasibility check
           
            # The starting solution is found just assigning one baggage per 
            # intermediate node (e.g there are 3 intermediate node, these
            # are the assignements --> b1 to I1, b2 to I2, b3 to I3, b4 to I1,
            # b5 to I2, b6 to I3... and so on). The reason is that we are just
            # looking for a feasible solution, so there are no conspumption
            # consideration until now

            # For each baggage we randomly shuffle the edges list. This 
            # beacuse here an edge is selected if it simply satisfies weight 
            # and capacity constraints, so if for any baggage the order to 
            # scan the edges is always the same, it ends up to send all the 
            # baggage to the first intermediate node until it is full, then 
            # to second one and so on... . This approach would not be fair and 
            # it would generate an infeasible solution because the first 
            # intermediate nodes would have too many baggage to manage.

            shuffled_edges = sorted(edges.values(), key=lambda x: random.random())

            # if i is larger, it means we exceeded the number of intermediate
            # nodes of the system. As said before, to ensure fairness we
            # assign i = 1 again, sothe next baggage can be sent again
            # to I1 if the last one was sent to x, where x is the last
            # intermediate node.
              
            if i > int_node:
                i = 1

            for edge in  shuffled_edges:
                
                # it is checked if the output node is an intermediate one, since
                # in this loop they are the only to be taken into account 
                # among all the "shuffled_edges". Then, if it is true, two 
                # constraints has to be satisfied: 1) Capacity 2) Weight,
                # meaning that the edge should have space to take another 
                # baggage and it should be able to support that total weight.

                if edge['info'].output_node == f'I{i}' and edge['info'].input_node == node[0]:
                    i+=1
                    if edge["info"].current_capacity_available - 1 >= 0 and edge["info"].current_weight_available - bag_w >= 0:
                        check_c = True

                if check_c == True:
                    
                    check_F = True
                    
                    # the baggage is deleted form the list of its source node.
                    del node[1]['baggage_list'][b]

                    # It is the consumption related to that single baggage
                    # sent to that specific edge.

                    baggage_consumption = bag_w * edge["info"].power

                    # "info_tuple" is the data structure defined as described
                    # in the 'first baggage_pathguess' explaination at line 46
                    
                    info_tuple = (edge["info"].output_node, edge["info"].id, baggage_consumption)
                    first_baggage_path_guess[bag.id].append(info_tuple)
                    
                    # the baggage is added to the baggage list of the node
                    # it will reach through the selcted edge

                    G.nodes[edge["info"].output_node]['baggage_list'][j] = bag

                    j += 1

                    break # we found the edge, we can break the loop
            
            if check_F == False: 
                
                # If no edge was found, the solution is infeasible for 
                # this graph

                first_baggage_path_guess = None
                return first_baggage_path_guess
    

    # Remember that node is ('node_name', {'demand: , 'baggage_list': {} } )
    # Now baggage go from intermediate nodes to destinations

    for node in intermediate: 
        
        #--------------------------------------------
        # We are numbering the baggage list of intermediate nodes from scratch 
        # because we need that the luggage go from index 1 to x, where x is the 
        # last luggage. Otherwise we have that in the previous for, the indices 
        # are given by j, which is a unique index for all luggage associated 
        # with any node, and in that case it is not possible to
        # scroll through the luggage as done in line 180.

        baggage = list(node[1]["baggage_list"].values())
        node[1]["baggage_list"].clear()

        for i, value in enumerate(baggage):
            node[1]["baggage_list"][i+1] = value
        #--------------------------------------------

        # len + 1 since baggage start from 1
        for b in range(1,len(node[1]['baggage_list'])+1): 
            bag = node[1]['baggage_list'][b]
            bag_w = bag.weight
            bag_d = bag.destination

            check_c = False # constraints check
            check_F = False # feasibility check
            
            for edge in edges.values():

                # == bag_d since tha baggage has to arrive to its
                # assigned destination. Then, the code is almost the same 
                # as before
            
                if edge['info'].output_node == bag_d and edge['info'].input_node == node[0]:

                    if edge["info"].current_capacity_available - 1 >= 0 and edge["info"].current_weight_available - bag_w >= 0:
                        check_c = True

                if check_c == True:

                    check_F = True

                    del node[1]['baggage_list'][b]
                    baggage_consumption = bag_w * edge["info"].power

                    info_tuple = (edge["info"].output_node, edge["info"].id, baggage_consumption)
                    first_baggage_path_guess[bag.id].append(info_tuple)
                    
                    G.nodes[edge["info"].output_node]['baggage_list'][j] = bag
                    
                    j += 1
                    
                    break
        
            if check_F == False:
                
                # No valid edge to reach the destination was found
                
                first_baggage_path_guess = None
                
                return first_baggage_path_guess
            
    return first_baggage_path_guess


# Calculate the total power consumption
def calculate_total_consumption(baggage_path):

    """ 
    Given the baggage path, it computes the total consupmtion of the 
    system just summing the consumption related to each baggage. 
    It is used in the local search function.
    
    """

    total_baggage_consumption = 0
    
    for bag_info in baggage_path.values():
        
        # consumption from source -> intermediate: 'bag_info[2][2]'
        # consumption from intermediate -> destination: 'bag_info[3][2]'

        single_baggage_consumption = bag_info[2][2] + bag_info[3][2] 

        total_baggage_consumption += single_baggage_consumption
    
    return total_baggage_consumption


def local_search_with_neighborhood(G, edges_list, max_iterations = 100):
    
    """
    Perform local search with neighborhood exploration to minimize power 
    consumption. Its arguments are: - G: The graph representing sources, 
    intermediates, and destinations. - edges_list: The list of edges in the 
    graph. - max_iterations: Maximum number of iterations to explore the 
    neighborhood. Then, it returns: - best_baggage_path: The best baggage path 
    found. - best_of: The best objective function (total power consumption) 
    found.

    """
   
    # it picks a first random feasible solution  
    current_baggage_path = first_feasible_solution_generator(G,edges_list)

    if current_baggage_path is None:
        # INFEASIBLE SOLUTION
        return None, None
    
    # current_baggage_path is the best feasible solution known so far.
    # Its of value is computed.

    best_baggage_path = current_baggage_path
    best_of = calculate_total_consumption(best_baggage_path)

    iteration = 0 # iterations for the local search
    
    while iteration < max_iterations:
        
        # neighbor_baggage_path is a copy of the best solution so far. It is 
        # done to find new possible solution without destroying the 
        # already existing one.

        neighbor_baggage_path = copy.deepcopy(best_baggage_path) 
        
        # Explore the neighborhood. How? just changing the intermediate nodes,
        # and so the edge selection, of a set of baggage. Morover, this baggage
        # portion is changed at each iteration to find always different 
        # solutions. If it is better, it is stored.
        # These are the steps:
        # 1) baggage shuffling
        # 2) Is the solution better? store it and shuffle again taking
        #    into account the new changes
        # 3) Is the solution worse? discard it and shuffle again to find
        #    a better one.
        # 4) Go to step 1 if iteration < max_iteration

        # Convert dictionary to list of tuples to perform shuffling
        shuffled_baggages = list(best_baggage_path.items())

        # Shuffle the list  
        random.shuffle(shuffled_baggages)  

        # Slice only 1/3 of the shuffled list. If we shuffled all the 
        # baggage list, the new solution would not be a "neighbor" solution.

        sliced_baggages = shuffled_baggages[:int(len(shuffled_baggages)/3)]

        for element in sliced_baggages:

            bag_id = element[0] # baggage id
            current_path = element[1] # baggage path 

            check_change = False # change edge check
            check_c = False # check constraint

            # Generate a neighbor by swapping this baggage to a 
            # different path (intermediate node)

            baggage = current_path[1] # baggage instance
           
            # swap the intermediate node for this baggage

            for edge_info in edges_list.values():
                
                edge = edge_info['info']
                
                # It enters the 'if' only if a change has not been performed yet
                if edge.input_node == current_path[0] and check_change is not True:  
                    
                    # A new edge is selected: Once it is verified that the input
                    # of the edge is the same, then we choose a different edge
                    # looking for a different edge output node with respect
                    # to the previous one.

                    if edge.output_node != current_path[2][0] and edge.current_capacity_available - 1 >= 0 and edge.current_weight_available - baggage.weight >= 0:  # Ensure we're not swapping to the same intermediate node
                        
                        # next_input will be the input of the edge that will
                        # lead to the final destination in the next for

                        next_input = edge.output_node

                        # update the new edge parameters

                        edge.current_capacity_available -= 1
                        edge.current_weight_available -= baggage.weight
                        baggage_consumption = edge.power * baggage.weight

                        # Perform the swap

                        neighbor_baggage_path[bag_id][2] = (edge.output_node, edge.id, baggage_consumption)

                        check_change = True

            # from the intermediate to the destination
            for edge_info in edges_list.values(): 

                edge = edge_info['info']
                
                # Here the new edge is selected juest verifying the constraints 
                # and the association with the final destination of the baggage

                if edge.output_node == baggage.destination and edge.input_node == next_input and check_c is not True: 

                    if edge.current_capacity_available - 1 >= 0 and edge.current_weight_available - baggage.weight >= 0:
                        check_c = True
                        baggage_consumption += edge.power * baggage.weight
                        edge.current_capacity_available -= 1
                        edge.current_weight_available -= baggage.weight
                        neighbor_baggage_path[bag_id][3] = (edge.output_node, edge.id, baggage_consumption)
            
        new_of = calculate_total_consumption(neighbor_baggage_path) 

        # If this neighbor is better, accept it
        if new_of < best_of:
            best_baggage_path = neighbor_baggage_path
            best_of = new_of
        
        iteration += 1
    
    return best_baggage_path, best_of
