'''
VRP with breaks and different start and end points.

Time matrix generated using distancematrix.ai's API.

Durations are in minutes.
'''

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import routing_matrix as rm


def create_data_model(time_matrix, num_vehicles, starts, ends, break_time, break_start_time, service_time=15, max_route_time=540, wait_time=10):
    '''
    Stores the data for the VRP problem.

    Parameters:
        time_matrix (list of list of int): Matrix where entry [i][j] represents the travel time from location i to j.
        num_vehicles (int): The number of vehicles available for the routes.
        starts (list of int): List of start indices for each vehicle.
        ends (list of int): List of end indices for each vehicle.
        break_time (int): Duration of the break in minutes.
        break_start_time (int): Time the break should start in minutes.
        service_time (int, optional): Service time at each location in minutes. Defaults to 15 min.
        max_route_time (int, optional): Max total time allowed for the completion of the route in minutes. Defaults to 540 min (9 hrs)
        wait_time (int, optional): Max total wait time in minutes. Defaults to 10 min. 

    Returns:
        dict: Data model containing the time matrix, number of vehicles, start and end points, and service times.
    '''
    data = {}
    data['matrix'] = time_matrix
    data['num_vehicles'] = num_vehicles 
    data['starts'] = starts 
    data['ends'] = ends 
    data['break_time'] = break_time 
    data['break_start_time'] = break_start_time 
    data['service_time'] = [service_time] * len(data['matrix']) 
    assert len(data['matrix']) == len(data['service_time'])
    #data['service_time'][data['depot']] = 0 
    data['max_route_time'] = max_route_time 
    data['wait_time'] = wait_time

    return data

def print_solution(manager, routing, solution):
    '''
    Prints the solution to the VRP problem.

    Parameters:
        manager (pywrapcp.RoutingIndexManager): Routing index manager used for mapping between nodes and indices.
        routing (pywrapcp.RoutingModel): Routing model instance used to solve the problem.
        solution (pywrapcp.Assignment): Solution returned by the solver.
    '''

    #print(f'Cost to be minimized: {solution.ObjectiveValue()}') 

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

def vrp_solver(data):
    """
    Solves the VRP problem using the OR-Tools library.

    Parameters:
        data (dict): Data model containing the time matrix, number of vehicles, start and end points, and service time.
    """

    # Routing Index Manager
    manager = pywrapcp.RoutingIndexManager(len(data['matrix']),
                                        data['num_vehicles'], 
                                        data['starts'],
                                        data['ends'])

    # Routing Model
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        '''Returns the travel time + service time between two nodes'''
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['matrix'][from_node][to_node] + data['service_time'][
            from_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Defining the cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Adding the Time dimension
    dimension = 'Time'
    routing.AddDimension(
        transit_callback_index,
        data['wait_time'],
        data['max_route_time'],  
        True,  # force start cumul to zero
        dimension)
    time_dimension = routing.GetDimensionOrDie(dimension)
    time_dimension.SetGlobalSpanCostCoefficient(10)

    # Adding breaks
    node_visit_transit = [0] * routing.Size()
    for index in range(routing.Size()):
        node = manager.IndexToNode(index)
        node_visit_transit[index] = data['service_time'][node]

    break_intervals = {}
    for v in range(manager.GetNumberOfVehicles()):
        break_intervals[v] = [
            routing.solver().FixedDurationIntervalVar(
                data['break_start_time'], 
                data['break_start_time'] + data['wait_time'],  
                data['break_time'], 
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


def main():

    # Problem specifications:
    num_vehicles = 4
    starts = [2, 6, 8, 5]
    ends = [0, 0, 0 , 0]
    break_time = 5
    break_start_time = 50
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

    time_matrix =  [
        [0, 6, 9, 8, 7, 3, 6, 2, 3, 2, 6, 6, 4, 4, 5, 9, 7],
        [6, 0, 8, 3, 2, 6, 8, 4, 8, 8, 13, 7, 5, 8, 12, 10, 14],
        [9, 8, 0, 11, 10, 6, 3, 9, 5, 8, 4, 15, 14, 13, 9, 18, 9],
        [8, 3, 11, 0, 1, 7, 10, 6, 10, 10, 14, 6, 7, 9, 14, 6, 16],
        [7, 2, 10, 1, 0, 6, 9, 4, 8, 9, 13, 4, 6, 8, 12, 8, 14],
        [3, 6, 6, 7, 6, 0, 2, 3, 2, 2, 7, 9, 7, 7, 6, 12, 8],
        [6, 8, 3, 10, 9, 2, 0, 6, 2, 5, 4, 12, 10, 10, 6, 15, 5],
        [2, 4, 9, 6, 4, 3, 6, 0, 4, 4, 8, 5, 4, 3, 7, 8, 10],
        [3, 8, 5, 10, 8, 2, 2, 4, 0, 3, 4, 9, 8, 7, 3, 13, 6],
        [2, 8, 8, 10, 9, 2, 5, 4, 3, 0, 4, 6, 5, 4, 3, 9, 5],
        [6, 13, 4, 14, 13, 7, 4, 8, 4, 4, 0, 10, 9, 8, 4, 13, 4],
        [6, 7, 15, 6, 4, 9, 12, 5, 9, 6, 10, 0, 1, 3, 7, 3, 10],
        [4, 5, 14, 7, 6, 7, 10, 4, 8, 5, 9, 1, 0, 2, 6, 4, 8],
        [4, 8, 13, 9, 8, 7, 10, 3, 7, 4, 8, 3, 2, 0, 4, 5, 6],
        [5, 12, 9, 14, 12, 6, 6, 7, 3, 3, 4, 7, 6, 4, 0, 9, 2],
        [9, 10, 18, 6, 8, 12, 15, 8, 13, 9, 13, 3, 4, 5, 9, 0, 9],
        [7, 14, 9, 16, 14, 8, 5, 10, 6, 5, 4, 10, 8, 6, 2, 9, 0],
    ]

    if time_matrix:
        data = create_data_model(time_matrix, num_vehicles, starts, ends, break_time, break_start_time) # Instance of the problem
        vrp_solver(data)
    else:
        print('Time matrix couldn\'t be generated')

if __name__ == '__main__':
    main()
            

