from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_data_model(time_matrix, num_vehicles, starts, ends, break_time=None, break_start_time=None, service_time=15, max_route_time=720, slack_time=10):
    '''
    Stores the data for the VRP problem.

    Args:
        time_matrix (list of list): Matrix where entry [i][j] represents the travel time from location i to j.
        num_vehicles (int): The number of vehicles available for the routes.
        starts (list of int): List of start indices for each vehicle.
        ends (list of int): List of end indices for each vehicle.
        break_time (int, optional): Duration of the break in minutes. Defaults to None.
        break_start_time (int, optional): Time the break should start in minutes. Defaults to None.
        service_time (int, optional): Service time at each location in minutes. Defaults to 15 min.
        max_route_time (int, optional): Max total time allowed for the completion of the route in minutes. Defaults to 720 min (12 hrs)
        slack_time (int, optional): Max slack time in minutes. Defaults to 10 min. 

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
    data['max_route_time'] = max_route_time
    data['slack_time'] = slack_time

    return data


def vrp_solver(data):
    '''
    Solves the VRP problem using the OR-Tools library.

    Args:
        data (dict): Data model containing the time matrix, number of vehicles, start and end points, and service time.
    '''

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
        return data['matrix'][from_node][to_node] + data['service_time'][from_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)

    # Defining the cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Adding the Time dimension
    dimension = 'Time'
    routing.AddDimension(
        transit_callback_index,
        data['slack_time'],
        data['max_route_time'],  
        True,  # force start cumul to zero
        dimension)
    time_dimension = routing.GetDimensionOrDie(dimension)
    time_dimension.SetGlobalSpanCostCoefficient(10)

    # Adding breaks
    if data['break_time'] is not None and data['break_start_time'] is not None:
        node_visit_transit = [0] * routing.Size()
        for index in range(routing.Size()):
            node = manager.IndexToNode(index)
            node_visit_transit[index] = data['service_time'][node]

        break_intervals = {}
        for v in range(manager.GetNumberOfVehicles()):
            break_intervals[v] = [
                routing.solver().FixedDurationIntervalVar(
                    data['break_start_time'], 
                    data['break_start_time'] + data['slack_time'],  
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


def print_solution(manager, routing, solution):
    '''
    Prints the solution to the VRP problem.

    Args:
        manager (pywrapcp.RoutingIndexManager): Routing index manager used for mapping between nodes and indices.
        routing (pywrapcp.RoutingModel): Routing model instance used to solve the problem.
        solution (pywrapcp.Assignment): Solution returned by the solver.
    '''

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