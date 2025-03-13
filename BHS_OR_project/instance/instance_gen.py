class Conveyor_belt:

    def __init__(self,capacity,weight,power, output_node, input_node, id):
        
        # max number of baggage on the belt
        self.max_capacity = capacity
        # max number of total baggage weight on the belt 
        self.max_weight = weight
        # power coefficient of the belt 
        self.power = power
        # identification number of the belt
        self.id = id

        # current weight on the belt
        self.current_weight_available = self.max_weight
        # current capacity on the belt
        self.current_capacity_available = self.max_capacity

        # start and end node of the belt
        self.output_node = output_node
        self.input_node = input_node

        # the following attirbutes are needed for the power consumption 
        # computation function. 
        self.total_weight = 0
        self.total_consumption = 0 #consumo complessivo ocnsiderando tutti i bagagli passati sul nastro
        self.baggage_consumption = 0 #consumo relativo all'aggiunta di un singolo bagaglio


    def power_consumption_computation(self,bagagge):
        
        """ This function is used to update the conveyor belt statistics any 
        time a new baggage is added to the line. Given a baggage, it returns
        the consumption related only to that specific bag 
        "self.baggage_consumption" and also the total conveyor belt consumption 
        "self.total_consumption" taking into account the weight contribution
        of all the other baggage on the edge."""

        # Weight update
        available_weight = self.current_weight_available - bagagge.weight
        self.current_weight_available = available_weight

        # Capacity update
        self.current_capacity_available -= 1

        # single baggage consumption given by the product between baggage weight
        # and power coefficient of the belt
        self.baggage_consumption = bagagge.weight*self.power

        # Total consumption on the belt, given by the total amount of baggage
        # weight on the Conveyor belt

        self.total_weight += bagagge.weight
        self.total_consumption = self.total_weight * self.power 

        return self.total_consumption, self.baggage_consumption

    
class Baggage:

    def __init__(self,weight,start,destination, id):
        
        # Baggage weight
        self.weight = weight

        # Baggage input node
        self.start = start

        # Baggage output node
        self.destination = destination

        # Baggage identification number
        self.id = id