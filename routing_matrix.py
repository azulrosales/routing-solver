import requests 

# distancematrix.ai API
API_KEY = 'yourKey'

def generate_matrix(locations, dimension='time'):
    '''
    Generates a time or distance matrix for a given set of locations using the Distance Matrix API (https://distancematrix.ai/distance-matrix-api)

    Parameters:
    - locations (list of str): List of locations (either addresses or coordinates can be used).
    - dimension (string): Dimension of the matrix to generate:
        - 'time' (default): generates a matrix of travel values (in minutes)
        - 'distance': generates a matrix of distances (in kilometers)

    Returns:
    - Matrix (list of list of int) of values or distances between each pair of locations.
        - If a route is not found '-1' is used as a placeholder.
        - If an error occurs in the API response '-1000' is used as a placeholder.

    '''

    # Joining the list into a string for the API request
    origins = "|".join(locations)
    destinations = "|".join(locations)

    # API request
    url = f'https://api.distancematrix.ai/maps/api/distancematrix/json?origins={origins}&destinations={destinations}&key={API_KEY}'
    # Response
    response = requests.get(url)
    data = response.json()

    if data['status'] == 'OK':

        print(data)

        matrix = []

        for row in data['rows']:
            values = []
            for element in row['elements']:
                if element['status'] == 'OK':
                    if dimension == 'time': # Generates time matrix 
                        values.append(round(element['duration']['value'] / 60)) # minutes
                    elif dimension == 'distance': # Generates distance matrix 
                        values.append(round(element['distance']['value'] / 1000)) # kilometers
                elif element['status'] == 'ZERO_RESULTS': # If no routes were found between these two locations (node)...
                    values.append(-1)
                else: # If an error occurs while processing this node...
                    values.append(-1000)
            matrix.append(values)

        return matrix

    else: # If there's an error when trying to connect with the API
        print(f'ERROR: received response status {data['status']}')

def print_matrix(matrix):
    '''Prints the given matrix'''
    for row in matrix:
        print(row)
