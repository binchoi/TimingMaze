import heapq
from os import system
import constants
from typing import List, Optional, Set, Tuple

from players.group5.player_map import PlayerMapInterface, SimplePlayerCentricMap, StartPosCentricPlayerMap
from players.group5.door import DoorIdentifier


def converge(current_pos : list, goal : list, turn : int, player_map: PlayerMapInterface) -> int:
	# print("Current Position: ", current_pos)
	# print("Goal Position: ", goal)

	print("Starting Dijkstra's algorithm...")

	path = dyjkstra(current_pos, goal, turn, player_map)

	print("Ending Dijkstra's algorithm...")
	# print("Path: ", path)
	return path[0] if path else constants.WAIT


def dyjkstra(current_pos : list, goal : list, turn : int, player_map: PlayerMapInterface) -> list:

	# turn_candidates = [turn]
	expected_turn = turn

	print("Turn Candidates: ", expected_turn)
	print("Current Position: ", current_pos)

	# Create a priority queue
	queue = []
	heapq.heappush(queue, (0, current_pos, expected_turn))


	# Create a dictionary to store the cost of each position
	costs = {tuple(current_pos): 0}

	# Create a set to store visited positions
	visited = set()

	# Create a dictionary to store the path to each position
	paths = {tuple(current_pos): []}

	# Create a dictionary to store the turns for each position
	turns = {tuple(current_pos): expected_turn}

	# While there are positions to explore
	while queue:
		print("Starting while loop...")

		# Get the position with the lowest cost
		current_cost, current_pos, expected_turn  = heapq.heappop(queue)

		print("Current Cost: ", current_cost)
		print("Current Position: ", current_pos)
		# print("Turn Candidates: ", turn_candidates)

		# If we have reached the goal, return the path
		if current_pos == goal:
			print("Current Position is the goal!")
			return paths[tuple(current_pos)]

		# If we have already visited this position, skip it
		if tuple(current_pos) in visited:
			continue

		# Mark the position as visited
		visited.add(tuple(current_pos))

		# Explore the neighbors
		for move in [constants.UP, constants.DOWN, constants.RIGHT, constants.LEFT, constants.WAIT]:

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
			elif move == constants.WAIT:
				print("Waiting...")
				neighbor = [current_pos[0], current_pos[1]]
				door = DoorIdentifier([current_pos[0], current_pos[1]], constants.DOWN)

			# Calculate the cost of the neighbor
			# TODO make a special function that calculates based on observations of wall intervals
			weight, new_expected_turn = add_weight(current_pos, neighbor, player_map.get_wall_freq_candidates(door), expected_turn)
			new_cost = current_cost + weight

			print("Weight: ", weight)
			print("New Cost: ", new_cost)
			print("New Expected Turn: ", new_expected_turn)

			# If the neighbor has not been visited or the new cost is lower, update the cost and add it to the queue
			if tuple(neighbor) not in visited and (tuple(neighbor) not in costs or new_cost < costs[tuple(neighbor)]):
				costs[tuple(neighbor)] = new_cost
				paths[tuple(neighbor)] = paths[tuple(current_pos)] + [move]
				heapq.heappush(queue, (new_cost, neighbor, new_expected_turn))

	# If we reach here, it means we could not find a path to the goal
	return None

def add_weight(start_pos, end_pos, wall_frequency_candidates, expected_turn) -> Tuple[float, int]:
	# calculates the likelihood of doors being open and average wait expected

	# if wall is always closed, return infinity
	if all(freq == 0 for freq in wall_frequency_candidates):
		print("Wall is always closed.")
		return float('inf'), 1 + expected_turn
	
	if start_pos == end_pos:
		print("Start position is the same as end position.")
		return 1, 1 + expected_turn
	
	cost = 0

	print("Wall Frequency Candidates: ", wall_frequency_candidates)
	# print("Turn Candidates: ", turn_candidates)

	q = 0

	for i in wall_frequency_candidates:
		# for j in turn_candidates:
		
		# if j == float('inf'):
		# 	continue
		if i == 0:
			print("Wall is always closed. 2")
			cost = float('inf')
		else:
			print("Calculating cost...")
			cost += i - (expected_turn % i)
		
		q += 1

		if q == 1000:
			print("Cost: ", cost)
	
	cost /= len(wall_frequency_candidates)
	# cost /= len(turn_candidates)

	cost += 1 # Add a base cost for moving
		
	# new_turn_candidates = []
	new_expected_turn = 0

	# if wall is always open, return 1
	
	# for turn in turn_candidates:
	for freq in wall_frequency_candidates:
		if freq == 0:
			print("Wall is always closed. 3")
			continue
			# new_turn_candidates.append(float('inf'))
		else:
			print("Calculating new turn candidates...")
			new_expected_turn += expected_turn + 1 + freq - (expected_turn % freq)
		new_expected_turn = int(new_expected_turn / len(wall_frequency_candidates))

	return cost, expected_turn




# NOTES:
# - see if we can hold onto the calucalted values by algorithm and modify them slightly with each turn as we learn more
# - the visited set should be modified to allow for backtracking if we find a better path
# maybe for each set of touching doors, make a dictionary that stores the door state and the cost of passing through it on any given turn


def compute_unobserved_door_weight() -> int:
	# calculates the likelihood of doors being open and average wait expected
	return 0

	