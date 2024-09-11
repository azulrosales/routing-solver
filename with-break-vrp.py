"""
VRP with breaks and different start and end points.

Pre-computed test time matrix.

Durations are in minutes.
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """Stores the data for the problem"""
    data = {}
    data['time_matrix'] = [
        [0, 27, 38, 34, 29, 13, 25, 9, 15, 9, 26, 25, 19, 17, 23, 38, 33], # travel time from location 0
        [27, 0, 34, 15, 9, 25, 36, 17, 34, 37, 54, 29, 24, 33, 50, 43, 60], # travel time from location 1, etc.
        [38, 34, 0, 49, 43, 25, 13, 40, 23, 37, 20, 63, 58, 56, 39, 77, 37],
        [34, 15, 49, 0, 5, 32, 43, 25, 42, 44, 61, 25, 31, 41, 58, 28, 67],
        [29, 9, 43, 5, 0, 26, 38, 19, 36, 38, 55, 20, 25, 35, 52, 33, 62],
        [13, 25, 25, 32, 26, 0, 11, 15, 9, 12, 29, 38, 33, 31, 25, 52, 35],
        [25, 36, 13, 43, 38, 11, 0, 26, 9, 23, 17, 50, 44, 42, 25, 63, 24],
        [9, 17, 40, 25, 19, 15, 26, 0, 17, 19, 36, 23, 17, 16, 33, 37, 42],
        [15, 34, 23, 42, 36, 9, 9, 17, 0, 13, 19, 40, 34, 33, 16, 54, 25],
        [9, 37, 37, 44, 38, 12, 23, 19, 13, 0, 17, 26, 21, 19, 13, 40, 23],
        [26, 54, 20, 61, 55, 29, 17, 36, 19, 17, 0, 43, 38, 36, 19, 57, 17],
        [25, 29, 63, 25, 20, 38, 50, 23, 40, 26, 43, 0, 5, 15, 32, 13, 42],
        [19, 24, 58, 31, 25, 33, 44, 17, 34, 21, 38, 5, 0, 9, 26, 19, 36],
        [17, 33, 56, 41, 35, 31, 42, 16, 33, 19, 36, 15, 9, 0, 17, 21, 26],
        [23, 50, 39, 58, 52, 25, 25, 33, 16, 13, 19, 32, 26, 17, 0, 38, 9],
        [38, 43, 77, 28, 33, 52, 63, 37, 54, 40, 57, 13, 19, 21, 38, 0, 39],
        [33, 60, 37, 67, 62, 35, 24, 42, 25, 23, 17, 42, 36, 26, 9, 39, 0],
    ]
    data['num_vehicles'] = 4 # number of available vehicles
    data['starts'] = [1, 2, 15, 16] # vehicle starting points
    data['ends'] = [0, 0, 0, 0] # vehicle ending points
    data['service_time'] = [15] * len(data['time_matrix']) # service time at each delivery location (15 min assumed)
    assert len(data['time_matrix']) == len(data['service_time'])
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
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], 
                                           data['starts'],
                                           data['ends'])

    # Routing Model
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        """Returns the travel time + service time between two nodes"""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node] + data['service_time'][
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