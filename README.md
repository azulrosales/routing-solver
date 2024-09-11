# VRP Solver

This program solves the Vehicle Routing Problem (VRP) with breaks and varying start and end points for vehicles.

## Overview

The VRP solver can handle scenarios where vehicles have specific starting and ending locations and need to take breaks during their routes. The time matrix, which is essential for the solver, can be generated using the `routing_matrix.generate_matrix(locations)` function.

## Features

- **Breaks Handling:** Incorporates breaks based on specified rules (e.g., EU regulations).
- **Custom Start/End Points:** Vehicles can start and end their routes at different locations.
- **Time Matrix Generation:** Use Distancematrix.ai's API to generate the required time matrix.

## Tools Used

- **Google OR-Tools:** For solving the VRP with constraints and breaks.
- **Distancematrix.ai's Distance Matrix API:** To generate the time matrix required for the solver.

## Files

### `routing_solver.py`

This script implements the VRP solver with breaks and varying start and end points. It generates and uses a time matrix created by `distancematrix.ai`'s API. The key functions include:

- **`create_data_model()`**: Defines the problem's data including the time matrix, number of vehicles, and their start/end points.
- **`print_solution(manager, routing, solution)`**: Prints the solution including routes, breaks, and total time.

### `routing_matrix.py`

This script handles the generation of the time matrix using the Distancematrix.ai API. It includes:

- **`generate_matrix(locations, dimension='time')`**: Generates a time or distance matrix for the given locations.
- **`print_matrix(matrix)`**: Prints the matrix in a readable format.

## Setup

1. **Install Dependencies:**
   Ensure you have the required libraries installed. You can use `pip` to install them if needed.

2. **API Key:**
   Replace the `API_KEY` in `routing_matrix.py` with your own API key from Distancematrix.ai.

3. **Run the Solver:**
   Execute `routing_solver.py` to solve the VRP with the specified parameters.




