import requests 

# distancematrix.ai API
API_KEY = 'yourKey'

def generate_matrix(locations: list[str], dimension: str = 'time') -> list[list]:
    '''
    Generates a time or distance matrix for a given set of locations using the Distance Matrix API.

    Args:
        locations (list of str): List of locations (either addresses or coordinates can be used).
        dimension (str, optional): Dimension of the matrix to generate:
            - 'time' (default): generates a matrix of travel values (in minutes)
            - 'distance': generates a matrix of distances (in kilometers)

    Returns:
        list of lists: Matrix of values or distances between each pair of locations.
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
                    raise KeyError(f'Missing expected key {e} in element.')

            matrix.append(values)

        return matrix

    except ValueError as e:
        # Handle errors in the API response
        raise ValueError(f'Error processing the API response: {e}')
    except Exception as e:
        # Handle any other unexpected errors
        raise Exception(f'Unexpected error: {e}')

 
def print_matrix(matrix: list[list]) -> None:
    '''
    Prints the given matrix row by row.

    Args:
        matrix (list of lists)

    Returns:
        None
    
    '''
    for row in matrix:
        print(row)
