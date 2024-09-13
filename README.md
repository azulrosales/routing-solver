# VRP Solver

This program solves the Vehicle Routing Problem (VRP) with breaks and varying start and/or end points for vehicles.

## Overview

The VRP solver can handle scenarios where vehicles have specific starting and ending locations and need to take breaks during their routes. The time matrix, which is essential for the solver, can be generated using the `routing_matrix.generate_matrix(locations)` function. The solver uses Google OR-Tools for optimization and Distancematrix.ai's API for distance/time calculations.

## Features

- **Breaks Handling:** Incorporates breaks based on specified rules (e.g., EU regulations).
- **Custom Start/End Points:** Vehicles can have different starting and/or ending locations.
- **Time Matrix Generation:** Uses Distancematrix.ai's API to generate the required time matrix.

## Tools Used

- **Google OR-Tools:** For solving the VRP (https://developers.google.com/optimization/routing).
- **Distancematrix.ai's Distance Matrix API:** To generate the time matrix required for the solver (https://distancematrix.ai/distance-matrix-api).

## Files

### `routing_solver.py`

This module provides the core functions needed to solve the VRP and display the solution:

- **`create_data_model()`**: Defines the VRP's data including the time matrix, number of vehicles, their start/end points, and break duration.
- **`vrp_solver()`**: Solves the VRP while handling breaks, time constraints, and varying start/end points.
- **`print_solution(manager, routing, solution)`**: Outputs the routes for each vehicle, including time spent and breaks.

### `routing_matrix.py`

This module handles the generation of the time matrix using the Distancematrix.ai API:

- **`generate_matrix(locations, dimension='time')`**: Generates a time or distance matrix for the given locations.
- **`print_matrix(matrix)`**: Prints the matrix in a readable format.

### `main.py`

This script reads the VRP problem configuration from a JSON file and solves the problem. It serves as a demo that can be run directly to test the solver.

- The JSON file should contain all necessary problem data, such as the locations and vehicle information.

## Setup

1. **Install Dependencies:**
   Ensure you have the required libraries installed. You can use `pip` to install them if needed.

2. **API Key:**
   Replace the `API_KEY` in `routing_matrix.py` with your own API key from Distancematrix.ai.
