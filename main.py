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


def validate_json(config):
    '''
    Validates the structure of the JSON file to ensure that it contains all the required keys for the VRP problem.

    Parameters:
        config (dict): JSON object loaded from a file.

    Returns:
        bool: True if the JSON is valid, raises an exception if invalid.
    '''     

    keys = {
        'num_vehicles': int,
        'starts': list,
        'ends': list,
        'locations': list,
        'break_time': (int, float, type(None)),
        'break_start_time': (int, float, type(None)),
        'service_time': (int, float, type(None)),  
        'max_route_time': (int, float, type(None)),  
        'wait_time': (int, float, type(None))  
    }

    for key, expected_type in keys.items():
        if key in config:  # Validate the expected types of the keys that are present
            if not isinstance(config[key], expected_type):
                raise TypeError(f'Invalid type for key "{key}". Expected {expected_type}, but got {type(config[key])}.')
        else:
            if not isinstance(expected_type, tuple):  # If the key is required but is not present
                raise ValueError(f'Missing required key: {key}')
            
    return True



def main():

    # Reading problem specifications from config.json:
    with open('config.json', 'r') as file:
        config = json.load(file)

    try:
        validate_json(config)
    
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

        time_matrix = rm.generate_matrix(locations)

        if time_matrix:
            data = rs.create_data_model(time_matrix, num_vehicles, starts, ends, break_time, break_start_time, service_time, max_route_time, slack_time) # Instance of the problem
            rs.vrp_solver(data)
        else:
            print('Time matrix couldn\'t be generated :(')

    except (ValueError, TypeError) as e:
        print(f'Invalid JSON format: {e}')


if __name__ == '__main__':
    main()
