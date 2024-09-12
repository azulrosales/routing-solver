import requests 

# distancematrix.ai API
API_KEY = 'yourKey'

import requests

def generate_matrix(locations, dimension='time'):
    '''
    Generates a time or distance matrix for a given set of locations using the Distance Matrix API.

    Args:
        locations (list of str): List of locations (either addresses or coordinates can be used).
        dimension (string): Dimension of the matrix to generate:
            - 'time' (default): generates a matrix of travel values (in minutes)
            - 'distance': generates a matrix of distances (in kilometers)

    Returns:
        Matrix (list of list) of values or distances between each pair of locations.
            - If a route is not found '-1' is used as a placeholder.
            - If an error occurs in the API response '-1000' is used as a placeholder.
    '''
    
    # Joining the list into a string for the API request
    origins = "|".join(locations)
    destinations = "|".join(locations)

    # API request
    url = f'https://api.distancematrix.ai/maps/api/distancematrix/json?origins={origins}&destinations={destinations}&key={API_KEY}'

    try:
        # Sending the API request
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX and 5XX)
        data = response.json()

        # Processing the response
        if data.get('status') != 'OK':
            raise ValueError(f'API Error: Received response status {data.get("status")}')

        matrix = []

        for row in data.get('rows', []):
            values = []
            for element in row.get('elements', []):
                try:
                    if element['status'] == 'OK':
                        if dimension == 'time':  # Generates time matrix 
                            values.append(round(element['duration']['value'] / 60))  # minutes
                        elif dimension == 'distance':  # Generates distance matrix 
                            values.append(round(element['distance']['value'] / 1000))  # kilometers
                    elif element['status'] == 'ZERO_RESULTS':  # No routes found
                        values.append(-1)
                    else:  # Error in processing node
                        values.append(-1000)
                except KeyError as e:
                    # Handle missing keys in the response
                    print(f'KeyError: Missing expected key {e} in element.')
                    values.append(-1000)
            matrix.append(values)

        return matrix

    except requests.RequestException as e:
        # Handle any errors that occur during the API request
        print(f'RequestException: An error occurred while making the API request: {e}')
        return None
    except ValueError as e:
        # Handle errors in the API response
        print(f'ValueError: {e}')
        return None
    except Exception as e:
        # Handle any other unexpected errors
        print(f'Unexpected error: {e}')
        return None

 
def print_matrix(matrix):
    '''
    Prints the given matrix row by row.

    Args:
    matrix (list of list)
    
    '''
    for row in matrix:
        print(row)
