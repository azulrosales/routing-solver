'''
VRP with breaks and different start and end points.

This script solves a Vehicle Routing Problem (VRP) with time constraints, 
where vehicles have different start and end points and mandatory break times. 
The goal is to minimize total travel time while considering travel times, 
service times at each location, and breaks for each vehicle.

Time matrix is generated using distancematrix.ai's API.

Durations are in minutes.
'''

import routing_solver as rs
import routing_matrix as rm
import json


def validate_required_keys(config: dict, required_keys: set) -> bool:
    '''
    Validates the presence of required keys in the provided dictionary.

    Args:
        config (dict): Dictionary to be validated.
        required_keys (set): Set of keys that must be present in the dictionary.

    Returns:
        bool:  True if all required keys are present, raises an exception if any are missing.
    '''

    missing_keys = required_keys - config.keys()
    if missing_keys:
        raise ValueError(f'Missing required keys: {", ".join(missing_keys)}')

    return True



def main():
    
    try:
        # Reading problem specifications from config.json:
        with open('config.json', 'r') as file:
            config = json.load(file)

        required_keys = {
            'num_vehicles',
            'starts',
            'ends',
            'locations',
        }

        validate_required_keys(config, required_keys)
    
        num_vehicles = config['num_vehicles']
        starts = config['starts']
        ends = config['ends']
        locations = config['locations']

        # Handling optional arguments 
        break_time = config.get('break_time')
        break_start_time = config.get('break_start_time')
        service_time = config.get('service_time', 15)
        max_route_time = config.get('max_route_time', 720)
        slack_time = config.get('slack_time', 10)

        try:
            time_matrix = rm.generate_matrix(locations)
        except (ValueError, Exception) as e:
            print(f'TIME MATRIX COULDN\'T BE GENERATED: {e}')


        time_matrix = [
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

        time_matrix = [
            [0, 1],
            [1, 4]
        ]

        if time_matrix:
            data = rs.create_data_model(time_matrix, num_vehicles, starts, ends, break_time, break_start_time, service_time, max_route_time, slack_time) # Instance of the problem
            rs.vrp_solver(data)
        else:
            print('Time matrix couldn\'t be generated.')

    except (ValueError, TypeError) as e:
        print(f'INVALID FORMAT: {e}')


if __name__ == '__main__':
    main()
