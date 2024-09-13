from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import warnings

def create_data_model(time_matrix: list[list[int]], 
                      num_vehicles: int, 
                      starts: list[int], 
                      ends: list[int], 
                      break_time: int | None = None, 
                      break_start_time: int | None = None, 
                      service_time: int = 15, 
                      max_route_time: int = 720, 
                      slack_time: int = 10) -> dict:
    '''
    Validates and constructs the data model for the VRP Solver.

    Args:
        time_matrix (lists of lists of int): Matrix of size nxn where n is the number of locations, and where entry [i][j] represents the travel time from location i to j.
        num_vehicles (int): The number of vehicles available for the routes.
        starts (list of int): List of start indices for each vehicle.
        ends (list of int): List of end indices for each vehicle.
        break_time (int, optional): Duration of the break in minutes. Defaults to None.
        break_start_time (int, optional): Time the break should start in minutes. Defaults to None.
        service_time (int, optional): Service time at each location in minutes. Defaults to 15 min.
        max_route_time (int, optional): Max total time allowed for the completion of the route in minutes. Defaults to 720 min (12 hrs)
        slack_time (int, optional): Max slack time in minutes. Defaults to 10 min. 

    Returns:
        dict: Data model containing the time matrix, number of vehicles, start and end points, service time, etc.
    '''
    
    # Data validaton
    if not isinstance(time_matrix, list) or not all(isinstance(row, list) for row in time_matrix):
        raise TypeError('time_matrix must be a list of lists.')
    
    if len(time_matrix) != len(time_matrix[0]):
        raise ValueError('time_matrix must be square (equal number of rows and columns).')
    
    if not all(isinstance(i, int) for row in time_matrix for i in row):
        raise ValueError('All elements of time_matrix must be integers.')
    
    if not isinstance(num_vehicles, int) or num_vehicles <= 0:
        raise ValueError('num_vehicles must be a positive integer.')
    
    if not isinstance(starts, list) or not all(isinstance(i, int) for i in starts) or len(starts) != num_vehicles: 
        raise ValueError(f'starts must be a list of {num_vehicles} integers.')
    
    if not isinstance(ends, list) or not all(isinstance(i, int) for i in ends) or len(ends) != num_vehicles: 
        raise ValueError(f'ends must be a list of {num_vehicles} integers.')
    
    if not all(0 <= i < len(time_matrix) for i in starts):
        raise ValueError('start index out of range.')
    
    if not all(0 <= i < len(time_matrix) for i in ends):
        raise ValueError('end index out of range.')

    if break_time is not None:
        if not isinstance(break_time, int) or break_time < 0:
            raise ValueError('break_time must be a non-negative integer.')
        if break_time >= max_route_time:
            warnings.warn('break_time should be less than max_route_time.')
    
    if break_start_time is not None:
        if not isinstance(break_start_time, int) or break_start_time < 0:
            raise ValueError('break_start_time must be a non-negative integer.')
        if break_start_time >= max_route_time:
            warnings.warn('break_start_time should be less than max_route_time.')
    
    if not isinstance(service_time, int) or service_time < 0:
        raise ValueError('service_time must be a non-negative integer.')
    
    if not isinstance(max_route_time, int) or max_route_time <= 0:
        raise ValueError('max_route_time must be a positive integer.')
    
    if not isinstance(slack_time, int) or slack_time < 0:
        raise ValueError('slack_time must be a non-negative integer.')
    
    data = {
        'matrix': time_matrix,
        'num_vehicles': num_vehicles,
        'starts': starts,
        'ends': ends,
        'break_time': break_time,
        'break_start_time': break_start_time,
        'service_time': [service_time] * len(time_matrix),
        'max_route_time': max_route_time,
        'slack_time': slack_time
    }

    return data


def vrp_solver(data: dict) -> None:
    '''
    Solves a Vehicle Routing Problem (VRP) with time constraints, where vehicles can have different start and/or end points and break times. 
    The objective is to minimize the total travel time while considering travel times, service times at each location, and breaks for each vehicle.

    Args:
        data (dict): Data model containing the time matrix, number of vehicles, start and end points, and optional parameters for breaks, service time, max route time, and slack time.
            Must include:
                - 'matrix': Time matrix (list of lists of int)
                - 'num_vehicles': Number of vehicles (int)
                - 'starts': List of start indices for each vehicle (list of int)
                - 'ends': List of end indices for each vehicle (list of int)
            Optional:
                - 'break_time': Duration of the break in minutes (int or None)
                - 'break_start_time': Time the break should start in minutes (int or None)
                - 'service_time': Service time at each location in minutes (int, default 15)
                - 'max_route_time': Max total time allowed for the completion of the route in minutes (int, default 720)
                - 'slack_time': Max slack time in minutes (int, default 10)

    Returns:
        None: The function prints the solution to the VRP problem or a message if no solution is found.
    '''

    # Routing Index Manager
    manager = pywrapcp.RoutingIndexManager(len(data['matrix']),
                                        data['num_vehicles'], 
                                        data['starts'],
                                        data['ends'])

    # Routing Model
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index: int, to_index: int) -> int:
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
    if data.get('break_time') is not None and data.get('break_start_time') is not None:
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


def print_solution(manager: pywrapcp.RoutingIndexManager, routing: pywrapcp.RoutingModel, solution: pywrapcp.Assignment) -> None:
    '''
    Prints the solution to the VRP problem.
        - The function prints information about any breaks scheduled for vehicles, including start time and duration.
        - For each vehicle, it prints the route taken, including the time at each node and the total route time.
        - It also prints the total time of all routes combined.

    Args:
        manager (pywrapcp.RoutingIndexManager): RoutingIndexManager used for mapping between nodes and indices.
        routing (pywrapcp.RoutingModel): RoutingModel instance used to solve the problem.
        solution (pywrapcp.Assignment): Solution returned by the solver.

    Returns:
        None: The function prints the routes and break details to the console.
    '''

    # Extracting breaks information from the solution
    intervals = solution.IntervalVarContainer()
    has_breaks = any(intervals.Element(i).PerformedValue() for i in range(intervals.Size()))

    # Print break information
    if has_breaks:
        print('\n Breaks:')
        for i in range(intervals.Size()):
            brk = intervals.Element(i)
            if brk.PerformedValue():
                print(f'{brk.Var().Name()}: ' + f'Start({brk.StartValue()}) Duration({brk.DurationValue()})')
            else:
                print(f'{brk.Var().Name()}: Unperformed')
        print('\n')

    # Print route information 
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