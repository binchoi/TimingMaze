import os
from constants import *
import constants
import numpy as np
import json
import argparse
from collections import deque as queue

def make_maze(args, seed):
    rng = np.random.default_rng(seed)
    start_pos = tuple(args.start_pos)
    end_pos = tuple(args.end_pos)
    map_frequencies = np.zeros((constants.map_dim, constants.map_dim, 4), dtype=int)

    # if maze is hard, set a minimum distance between start and end positions
    if not args.easy:
        dist = np.linalg.norm(start_pos - end_pos)
        if dist < 30:
            raise Exception("Start and end position are too close (less than 30)")
        
    # check if start and end positions are in range
    for i in start_pos:
        if i < 0 or i >= constants.map_dim:
            raise Exception("Start position out of range")
        
    for i in end_pos:
        if i < 0 or i >= constants.map_dim:
            raise Exception("End position out of range")

    # start and end position can't be the same    
    if start_pos == end_pos:
        raise Exception("Start and end positions are the same")
    
    # check if closed probability is too large
    if args.closed_prob >= 0.2:
        raise Exception("Closed probability too large")

    # generate maze
    for i in range(constants.map_dim):
        for j in range(constants.map_dim):
            for k in range(4):
                if rng.random() < args.closed_prob:
                    map_frequencies[i][j][k] = 0
                else:
                    map_frequencies[i][j][k] = rng.integers(1, args.max_door_frequency)
    
    # make sure the borders are closed
    for i in range (constants.map_dim):
        map_frequencies[0][i][constants.LEFT] = 0
        map_frequencies[constants.map_dim-1][i][constants.RIGHT] = 0
        map_frequencies[i][0][constants.UP] = 0
        map_frequencies[i][constants.map_dim-1][constants.DOWN] = 0

    return map_frequencies, start_pos, end_pos
    
def validate_maze(args, map_frequencies):
    # Check the size of the map
    if map_frequencies.shape != (constants.map_dim, constants.map_dim, 4):
        print("Error with map size")
        return False

    # Check that all doors have a frequency between 0 and max_door_frequency
    for i in range(constants.map_dim):
        for j in range(constants.map_dim):
            for k in range(4):
                if map_frequencies[i][j][k] < 0 or map_frequencies[i][j][k] > args.max_door_frequency:
                    print("Error with frequency")
                    return False

    # Check that all boundary doors have n=0 in map_frequencies.
    for i in range(constants.map_dim):
        if map_frequencies[0][i][constants.LEFT] != 0:
            print("Error with UP")
            return False
        if map_frequencies[constants.map_dim-1][i][constants.RIGHT] != 0:
            print("Error with DOWN")
            return False
        if map_frequencies[i][0][constants.UP] != 0:
            print("Error with LEFT")
            return False
        if map_frequencies[i][constants.map_dim-1][constants.DOWN] != 0:
            print("Error with RIGHT")
            return False

    # Check if all cells are reachable from one-another
    # Create an undirected graph and check if the map is valid by looking for islands in the graph.

    # Create a graph of the map with the doors as edges and a valid path if both doors are open at anytime.
    graph = np.zeros((constants.map_dim, constants.map_dim, 4), dtype=int)

    for i in range(constants.map_dim):
        for j in range(constants.map_dim):
            for k in range(4):
                if map_frequencies[i][j][k] != 0:
                    if k == constants.LEFT:
                        if i > 0 and map_frequencies[i-1][j][constants.RIGHT] != 0:
                            graph[i][j][k] = 1
                    elif k == constants.RIGHT:
                        if i < constants.map_dim-1 and map_frequencies[i+1][j][constants.LEFT] != 0:
                            graph[i][j][k] = 1
                    elif k == constants.DOWN:
                        if j < constants.map_dim-1 and map_frequencies[i][j+1][constants.UP] != 0:
                            graph[i][j][k] = 1
                    elif k == constants.UP:
                        if j > 0 and map_frequencies[i][j-1][constants.DOWN] != 0:
                            graph[i][j][k] = 1


    # Create a visited array to keep track of visited cells
    visited = np.zeros((constants.map_dim, constants.map_dim), dtype=int)

    # Create a queue to perform BFS traversal
    q = queue()
    q.append((0, 0))
    visited[0][0] = 1
    visited_count = 0

    # Perform BFS traversal
    # print("Validating reachability of all cells...")

    dRow = [-1, 0, 1, 0]
    dCol = [0, -1, 0, 1]

    while len(q) > 0:
        cell = q.popleft()
        row = cell[0]
        col = cell[1]
        visited_count += 1

        # Check for all the four doors,
        for door_type in range(4):
            if graph[row][col][door_type] == 1:
                # Get the adjacent cell
                adj_x = row + dRow[door_type]
                adj_y = col + dCol[door_type]
                if 0 <= adj_x < constants.map_dim and 0 <= adj_y < constants.map_dim and visited[adj_x][adj_y] == 0:
                    q.append((adj_x, adj_y))
                    visited[adj_x][adj_y] = 1

    return visited_count == constants.map_dim * constants.map_dim

def save_maze(args, map_frequencies, start_pos, end_pos):
    data = {
        "frequencies": map_frequencies.tolist(),
        "start_pos": list(start_pos),
        "end_pos": list(end_pos)
    }

    file_name = os.path.join(args.outdir, args.file_name)
    with open(file_name, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print(f"JSON file '{file_name}' created successfully.")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_door_frequency", "-m", type=int, default=5,
                        help="Value between 1 and 100 (including 1)")
    parser.add_argument("--closed_prob", "-cp", type=float, default=0.05, 
                        help="Probability that a door is permanently closed")
    parser.add_argument("--start_pos", "-sp", type=int, nargs=2, required=True, help="Starting position")
    parser.add_argument("--end_pos", "-ep", type=int, nargs=2, required=True, help="Target position")
    parser.add_argument("--easy", "-e", type=bool, default=True, help="Difficulty of maze")
    # parser.add_argument("--seed", "-s", type=int, default=2, help="Seed used by random number generator")
    parser.add_argument("--file_name", "-f", type=str, default="group4", help="File name of maze")
    parser.add_argument("--outdir", "-o", type=str, default="maps/default/", 
                        help="Output directory to save the maze")
    args = parser.parse_args()

    for i in range(100):
        map_frequencies, start_pos, end_pos = make_maze(args, i)

        if validate_maze(args, map_frequencies):
            save_maze(args, map_frequencies, start_pos, end_pos)
            print(f"Maze created and saved successfully with seed {i}...")
            break