"""
VRP with breaks and different start and end points.

Time matrix generated using distancematrix.ai's API.

Durations are in minutes.
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import routing_matrix as rm


locations = [
    'Arzak, Avenida Alcalde Elósegui, 273, 20015 Donostia, Gipuzkoa, Spain',  
    'Akelarre, Paseo Padre Orcolaga, 56, 20008 Donostia, Gipuzkoa, Spain',  
    'Mugaritz, Aldura Aldea, 20, 20100 Errenteria, Gipuzkoa, Spain',   
    'Amelia by Paulo Airaudo, Calle Prim, 34, 20006 Donostia, Gipuzkoa, Spain',   
    'Narru, Zubieta Kalea, 56, 20007 Donostia, Gipuzkoa, Spain',  
    'Kokotxa, Calle del Campanario, 11, 20003 Donostia, Gipuzkoa, Spain',
    'Mapa Verde, Calle Trueba, 4, 20001 Donostia, Gipuzkoa, Spain',
    'La Cuchara de San Telmo, Calle 31 de Agosto, 28, 20003 Donostia, Gipuzkoa, Spain',
    'Beti Jai Berria, Calle Fermin Calbeton, 22, 20003 Donostia, Gipuzkoa, Spain'
]

time_matrix = rm.generate_matrix(locations)
rm.print_matrix(time_matrix)

def create_data_model():
    """Stores the data for the problem"""
    data = {}
    data['matrix'] = time_matrix
    data['num_vehicles'] = 3 # number of available vehicles
    data['starts'] = [1, 2, 4] # vehicle starting points
    data['ends'] = [0, 0, 0] # vehicle ending points
    data['service_time'] = [15] * len(data['matrix']) # service time at each delivery location (15 min assumed)
    assert len(data['matrix']) == len(data['service_time'])
    #data['service_time'][data['depot']] = 0 
    return data

def print_solution(manager, routing, solution):
    """Prints solution on console"""
    print(f'Cost to be minimized: {solution.ObjectiveValue()}') 

    print('Breaks:')
    intervals = solution.IntervalVarContainer()
    for i in range(intervals.Size()):
        brk = intervals.Element(i)
        if brk.PerformedValue():
            print(f'{brk.Var().Name()}: ' +
                  f'Start({brk.StartValue()}) Duration({brk.DurationValue()})')
        else:
            print(f'{brk.Var().Name()}: Unperformed')

    time_dimension = routing.GetDimensionOrDie('Time')
    total_time = 0
    for vehicle_id in range(manager.GetNumberOfVehicles()):
        index = routing.Start(vehicle_id)
        plan_output = f'Route for vehicle {vehicle_id}:\n'
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += f'{manager.IndexToNode(index)} '
            plan_output += f'Time({solution.Value(time_var)}) -> '
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += f'{manager.IndexToNode(index)} '
        plan_output += f'Time({solution.Value(time_var)})\n'
        plan_output += f'Time of the route: {solution.Value(time_var)}min\n'
        print(plan_output)
        total_time += solution.Value(time_var)
    print(f'Total time of all routes: {total_time}min')


def main():
    data = create_data_model() # Instance of the problem

    # Routing Index Manager
    manager = pywrapcp.RoutingIndexManager(len(data['matrix']),
                                           data['num_vehicles'], 
                                           data['starts'],
                                           data['ends'])

    # Routing Model
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        """Returns the travel time + service time between two nodes"""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['matrix'][from_node][to_node] + data['service_time'][
            from_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Defining the cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Adding the Time dimension
    dimension = 'Time'
    wait_time = 10 # optional waiting time
    max_route_time = 540 # max total time per vehicle (540 min = 9 hrs in this case)

    routing.AddDimension(
        transit_callback_index,
        wait_time,
        max_route_time,  
        True,  # force start cumul to zero
        dimension)
    
    time_dimension = routing.GetDimensionOrDie(dimension)
    time_dimension.SetGlobalSpanCostCoefficient(10)

    # Breaks
    # EU regulation for drivers: 45 min break after 4.5 hrs of driving. 9 hrs of driving allowed per day. 
    node_visit_transit = [0] * routing.Size()
    for index in range(routing.Size()):
        node = manager.IndexToNode(index)
        node_visit_transit[index] = data['service_time'][node]

    break_intervals = {}
    for v in range(manager.GetNumberOfVehicles()):
        break_intervals[v] = [
            routing.solver().FixedDurationIntervalVar(
                270,  # min start time of the break: after 4.5 hrs
                280,  # start max: after 4.66 hrs
                45,  # duration: 45 min
                False,  # optional: no
                f'Break for vehicle {v}')
        ]
        time_dimension.SetBreakIntervalsOfVehicle(
            break_intervals[v],  # breaks
            v,  # vehicle index
            node_visit_transit)

    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    # search_parameters.log_search = True
    search_parameters.time_limit.FromSeconds(2)

    # Solving the problem
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print_solution(manager, routing, solution)
    else:
        print('No solution found :(')

if __name__ == '__main__':
    main()