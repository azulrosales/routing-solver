"""
VRP with breaks and different start and end points.

Time matrix generated using distancematrix.ai's API.

Durations are in minutes.
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import routing_matrix as rm
import csv

def load_vrp_data(file_path):
    '''Loads VRP data from a CSV file'''
    locations, starts_indices, end_indices = [], [], []
    num_vehicles = 0 

    with open(file_path, mode='r') as file:
        content = csv.reader(file, delimeter=';')
        for row in content:
            if row[0] == 'start':
                locations.append(row[1])
                starts_indices.append(int(row[2]))
            if row[0] == 'end':
                locations.append(row[1])
                starts_indices.append(int(row[2]))
            

