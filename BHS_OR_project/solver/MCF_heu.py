from instance.instance_gen import *

def no_selected_edge_computation(edge_id, edges, baggage):

    """ This function is called in the min_cost_computation to bring again belt 
    statistics to the previous condition. This is important since any baggage
    path is chosen according to the conveyor belt condition. This means that
    for each baggage all belt statistics are momentaneously updated 
    supposing that the bag is sent through that belt. Then, if that belt is 
    not selected, statistics go back to their previous values using this 
    function. It takes as input the id of the edge that is not selected 
    "edge_id", the list of all the graph edges 'edges'
    and the evaluated baggage 'baggage'. """

    for edge in edges.values():
        if edge_id == edge["info"].id:
            edge["info"].total_consumption = edge["info"].total_consumption - edge["info"].baggage_consumption
            edge["info"].total_weight -= baggage.weight
            edge["info"].current_capacity_available += 1
            edge["info"].current_weight_available = edge["info"].current_weight_available + baggage.weight
                

def min_cost_computation(G,edges):

    """ This function aims to compute the best path for each baggage in terms of 
    energy consumption related to conveyor belts use. The approach is based
    on evaluating nodes baggage in the following order --> input, intermediate,
    output. Then, inside a node buffer, FIFO is the used policy. It receives
    the generated graph 'G' and the edges_list 'edges' as input parameters. They
    are both defined in the 'graph_gen' code. Then, it returns a dictionary 
    "baggage_best path" reporting the path selected for each baggage and the 
    relative consumption. """

    # Step 1: organization of the nodes list. Even if nodes information are 
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

    # Step 2: Association of each baggage to its best path. Three for loop: 
    # the first one iterates on each input or intermediate node, the second one
    # scans all the node baggage, while the third one iterates on any edge
    # linked to the considered node according to select the best edge in terms of
    # energy consumotion for that given baggage. Moreover, there are threshold
    # values associated to each intermediate node that ensure an edge selection
    # that prevent congestion even if it means more energy consumption. This 
    # is done to protect the system from failures.

    # baggage_best_path is a dictionary {'baggage_id':["starting node", 
    # ('next node', conveyor belt used to reach the next node,
    # single baggage consumption)] }. It is used as reference to track
    # all the baggage movements. It is very important.
      
    baggage_best_path = {}

    # 'j' is a "total counter" used as key of each G.nodes node.
    j = 1  
  
  # node is ('node_name', {'demand: , 'baggage_list': {} } )
    for node in input: 

        # iteration over baggage of the node, where the stop point is len + 1 
        # since baggage counter j start from 1

        for b in range(1,len(node[1]['baggage_list'])+1):
            
            bag = node[1]['baggage_list'][b]
            bag_w = bag.weight
            bag_d = bag.destination
            bag_s = bag.start

            baggage_best_path[bag.id] = []
            baggage_best_path[bag.id].append(bag_s)
            

            # 'possible edge' is a dictionary with the following structure:
            # { key: ('next_node', edge id to reach the node, single baggage
            # consumption), value: total consumption on the belt)}. It is used
            # to store all these data supposing that the bag is added to that 
            # belt. Indeed, if it is done for all the edges starting from 
            # the node of the bag we are taking into account, 'possible_edge'
            # will contain an overview about the impact that the bag would
            # have on any edge it can potentially select to reach the next node.
            # As for secure_possible_edge, it is the same of possible_edge but
            # it stores information only related to those edge that are 
            # almost full. This dictionary is taken into acoount only when
            # 'possible edge' is empty, meaning that all the possible conveyor
            # belts are almost full. 

            possible_edge = {}
            secure_possible_edge = {}
            check_c = False # constraints check
            security_check = False # bottleneck prevention check
            i = 1
            int_nodes = len(intermediate)
            
            for edge in edges.values():

                #'c_threshold' and 'w_threshold' are values associated to the 
                # output edge capacity and weight, considering that the edge
                # starts from the intermedite node 'i' and it is linked to 
                # the destination 'bag_d' of the bag. They are used to 
                # leave a safe amount of space on the belt, so that the
                # intermediate node 'i' is selcted by the sources only if 
                # it can support the traffic towards the bag assigned 
                # destination. 
                 
                if i <= int_nodes:
                    c_threshold = int(G.nodes[f'I{i}']['output_edge_capacity'][bag_d]) - 10 # DA SISTEMARE CON VALORI ADEGUATI PER VERIFICHE SU POCHI BAGAGLI 
                    w_threshold = int(G.nodes[f'I{i}']['output_edge_weight'][bag_d]) - (10+25/2) # DA SISTEMARE CON VALORI ADEGUATI PER VERIFICHE SU POCHI BAGAGLI 

                # it is checked if the output node is an intermediate one, since
                # in this loop they are the only to be taken into account 
                # among all the "edges.values()". Then, if it is true, two 
                # constraints has to be satisfied: 1) Capacity 2) Weight,
                # meaning that the edge should have space to take another 
                # baggage and it should be able to support that total weight.
                # Then, if the check is true, we add to 'possible_edge'
                # the potential consumption of that edge with that new baggage.
                # However, if the total amount of baggae, sent through the node
                # 'i' and directed towards the destination 'bag_d', is too high,
                # that edge linking 'i' to 'bag_d' is not added to 'possible_edge'
                # but to 'secure_possible_edge', since 'security_check' is false.
                # That link is taken again into account only when 'possible_edge'
                # becomes empty, so that the energy consumption comparison
                # has to be performed between the edges that are all almost
                # congested. To conclude, this approach leads to the selection
                # of an adge that is not necessary the best in terms of energy
                # consumption if it is risky for the system stability.

                if edge['info'].output_node == f'I{i}' and edge['info'].input_node == node[0]:

                    # constraint check

                    if edge["info"].current_capacity_available - 1 >= 0 and edge["info"].current_weight_available - bag_w >= 0:
                        check_c = True
                    else:
                        check_c = False

                    # security check

                    if G.nodes[f'I{i}']["current_edge_capacity"][bag_d] + 1 <= c_threshold and G.nodes[f'I{i}']["current_edge_weight"][bag_d] + bag_w <= w_threshold:
                        security_check = True
                    else:
                        security_check = False
                
                    # possible edge addition

                    if check_c == True and security_check == True:
                        # we call the power_consumption_computation function
                        # defined in instance_gen
                        total_consumption, baggage_consumption = edge["info"].power_consumption_computation(bag)
                        possible_edge[(edge["info"].output_node, edge["info"].id, baggage_consumption)] = (total_consumption) 
                    
                    # security edge addition

                    if check_c == True and security_check == False:
                            total_consumption, baggage_consumption = edge["info"].power_consumption_computation(bag)
                            secure_possible_edge[(edge["info"].output_node, edge["info"].id, baggage_consumption)] = (total_consumption)

                    i+=1
                    
            if possible_edge:
                # this portion of code is executed only if there are edges 
                # satisfying the constraints discussed before.

                # We delete the baggage information from the node that the 
                # baggage is leaving
                del node[1]['baggage_list'][b] 
                
                # next_node is the tuple between the 'possible_edge' keys
                # associated to the lowest total consumption value. It is the 
                # heart of the algorithm, where the best selection is performed,
                # ensuring the best path in terms of energy consumption.

                next_node = min(possible_edge, key=possible_edge.get) #get restituisce i valori associati alle chiavi
                
                # we add to 'baggage_best_path' the tuple next node associated
                # to the bag.id, so that we can store all the information 
                # abount the next hop of the bag, the edge exploited and its cost 
                baggage_best_path[bag.id].append(next_node) 

                # We move the bag to the next node of the graph
                G.nodes[next_node[0]]['baggage_list'][j] = bag

                # output node link parametrs updating 
                G.nodes[next_node[0]]["current_edge_weight"][bag_d] += bag_w
                G.nodes[next_node[0]]["current_edge_capacity"][bag_d] += 1

                # For those edges that are not selected, the updated information
                # have to go back to their previous values, since the impact
                # of the bag on those edges does not have to be considered.
                 
                for edge in possible_edge.keys():
                    if edge[0] != next_node[0]:
                        no_selected_edge_computation(edge[1],edges,bag)

                j += 1

            elif secure_possible_edge:
                
                # This portion of code is executed only when there are no more 
                # safe 'possible edge', but its working principle is still
                # the same of the 'if' statement at line 187.
            
                del node[1]['baggage_list'][b] 

                next_node = min(secure_possible_edge, key=secure_possible_edge.get)
                
                baggage_best_path[bag.id].append(next_node) 
                
                G.nodes[next_node[0]]['baggage_list'][j] = bag
                G.nodes[next_node[0]]["current_edge_weight"][bag_d] += bag_w
                G.nodes[next_node[0]]["current_edge_capacity"][bag_d] += 1
                 
                for edge in secure_possible_edge.keys():
                    if edge[0] != next_node[0]:
                        no_selected_edge_computation(edge[1],edges,bag)

                j += 1
            

            else:
                # the code arrives here if possible_edge is empty, so there
                # are no edges satisfying the constraints, so the solution
                # is infeasible
                baggage_best_path = None
                return baggage_best_path
                

    
    # Now, the same is done to move baggage from intemrediate nodes to their
    # destination. There are just few differences, so we could merge these
    # two portion of the code. However, for a better readability we 
    # decided to keep them separated. 

    # Remember that node is ('node_name', {'demand: , 'baggage_list': {} } )
    for node in intermediate: 
        
        #--------------------------------------------
        # We are numbering the baggage list of intermediate nodes from scratch 
        # because we need that the luggage go from index 1 to x, where x is the 
        # last luggage. Otherwise we have that in the previous for, the indices 
        # are given by j, which is a unique index for all luggage associated 
        # with any node, and in that case it is not possible to
        # scroll through the luggage as done in line 178.

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

            possible_edge = {}
            check_c = False
                        
            for edge in edges.values():

                # == bag_d since tha baggage has to arrive to its
                # assigned destination. Then, the code is almost the same as before

                if edge['info'].output_node == bag_d and edge['info'].input_node == node[0]: 
                    
                    if edge["info"].current_capacity_available - 1 >= 0 and edge["info"].current_weight_available - bag_w >= 0:
                        check_c = True
                
                # Here there is no "possible_edge". From each intermediate
                # node there is only one possible selection corresponding to
                # the destination node

                    if check_c == True:
                        total_consumption, baggage_consumption = edge["info"].power_consumption_computation(bag) 
                        del node[1]['baggage_list'][b] 
                        next_node = (edge["info"].output_node, edge["info"].id, baggage_consumption)
                        baggage_best_path[bag.id].append(next_node)
                        G.nodes[next_node[0]]['baggage_list'][j] = bag
    
                        j += 1

            if check_c == False:
                # INFEASIBLE SOLUTION
                baggage_best_path = None
                return baggage_best_path
    
    
    return baggage_best_path
