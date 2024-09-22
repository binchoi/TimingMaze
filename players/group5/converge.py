import heapq
import logging
import math
from os import system
import constants
from typing import List, Optional, Set, Tuple

from players.group5.player_map import PlayerMapInterface, SimplePlayerCentricMap, StartPosCentricPlayerMap
from players.group5.door import DoorIdentifier


def converge(current_pos : list, goal : list[list[int]], turn : int, player_map: PlayerMapInterface, max_door_frequency) -> int:

	path = dyjkstra(current_pos, goal, turn, player_map,  max_door_frequency)

	print("path: ", path)
	print("Direction: ", path[0])

	return path[0] if path else None


def dyjkstra(current_pos : list, goal : list[list[int]], turn : int, player_map: PlayerMapInterface,  max_door_frequency) -> list:

	# Create a priority queue
	queue = []
	heapq.heappush(queue, (0, current_pos, turn))

	# Create a dictionary to store the cost of each position
	costs = {tuple(current_pos): 0}

	# Create a set to store visited positions
	visited = set()

	# Create a dictionary to store the path to each position
	paths = {tuple(current_pos): []}

	# Create a dictionary to store the turns for each position
	turns = {tuple(current_pos): turn}

	# While there are positions to explore
	while queue:
		# Get the position with the lowest cost
		current_cost, current_pos, expected_turn  = heapq.heappop(queue)

		# If we have reached the goal, return the path
		if current_pos in goal:
			return paths[tuple(current_pos)]

		# If we have already visited this position, skip it
		if tuple(current_pos) in visited:
			continue

		# Mark the position as visited
		visited.add(tuple(current_pos))

		# Explore the neighbors
		for move in [constants.UP, constants.DOWN, constants.RIGHT, constants.LEFT]:

			if move == constants.LEFT:
				neighbor = [current_pos[0] - 1, current_pos[1]]
				door = DoorIdentifier([current_pos[0], current_pos[1]], constants.LEFT)
			elif move == constants.UP:
				neighbor = [current_pos[0], current_pos[1] - 1]
				door = DoorIdentifier([current_pos[0], current_pos[1]], constants.UP)
			elif move == constants.RIGHT:
				neighbor = [current_pos[0] + 1, current_pos[1]]
				door = DoorIdentifier([current_pos[0], current_pos[1]], constants.RIGHT)
			elif move == constants.DOWN:
				neighbor = [current_pos[0], current_pos[1] + 1]
				door = DoorIdentifier([current_pos[0], current_pos[1]], constants.DOWN)

			# Calculate the cost of the neighbor
			# TODO make a special function that calculates based on observations of wall intervals
			# weight, new_expected_turn = add_weight(current_pos, neighbor, player_map.get_wall_freq_candidates(door), expected_turn)

			print("current_pos: ", current_pos)
			print("neighbor: ", neighbor)
			print("door: ", door)

			weight, new_expected_turn = calculate_weighted_average(expected_turn, player_map.get_wall_freq_candidates(door), max_door_frequency)

			print ("weight: ", weight)

			if weight == 1e20:
				# print("SKIPPED MOVE: ", move)
				continue  # Skip this move if the door is closed
			
			new_cost = current_cost + weight

			# If the neighbor has not been visited or the new cost is lower, update the cost and add it to the queue
			if tuple(neighbor) not in visited and (tuple(neighbor) not in costs or new_cost < costs[tuple(neighbor)]):
				costs[tuple(neighbor)] = new_cost
				paths[tuple(neighbor)] = paths[tuple(current_pos)] + [move]
				heapq.heappush(queue, (new_cost, neighbor, new_expected_turn))

	# If we reach here, it means we could not find a path to the goal
	return None


# # NOTES:
# # - see if we can hold onto the calucalted values by algorithm and modify them slightly with each turn as we learn more
# # - the visited set should be modified to allow for backtracking if we find a better path
# # maybe for each set of touching doors, make a dictionary that stores the door state and the cost of passing through it on any given turn
# def compute_unobserved_door_weight() -> int:
	# calculates the likelihood of doors being open and average wait expected
	return 0

def calculate_weighted_average(current_turn, candidates, max_door_frequency):
    """
    Calculate a weighted average cost for traversing a door based on the current turn
    and the candidate turns when the door might open. Also return the expected turn.

    Parameters:
    - current_turn (int): The current turn.
    - candidates (list): A list of candidate turns when the door might open.

    Returns:
    - average_weight (float): The weighted average cost for passing through the door.
    - expected_turn (int): The next expected turn when the door will open.
    """

    print(candidates)

    if all(candidate == 0 for candidate in candidates):
        return 1e20, current_turn + 1e20

    weights = []
    total_weight = 0
    weighted_sum = 0
    next_expected_turn = None
    avg_distance = 0

    for candidate in candidates:
        if candidate == 0:
            candidate = max_door_frequency
		
        distance = candidate - (current_turn % candidate)
        avg_distance += distance


    avg_distance /= len(candidates)

    return avg_distance, round(avg_distance) + current_turn

def expected_turn_cands():
	pass