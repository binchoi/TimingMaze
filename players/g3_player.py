from audioop import reverse

import numpy as np
import logging

import constants
from timing_maze_state import TimingMazeState


class Player:
    def __init__(self, rng: np.random.Generator, logger: logging.Logger,
                 precomp_dir: str, maximum_door_frequency: int, radius: int) -> None:
        """Initialise the player with the basic information

            Args:
                rng (np.random.Generator): numpy random number generator, use this for same player behavior across run
                logger (logging.Logger): logger use this like logger.info("message")
                maximum_door_frequency (int): the maximum frequency of doors
                radius (int): the radius of the drone
                precomp_dir (str): Directory path to store/load pre-computation
        """

        # precomp_path = os.path.join(precomp_dir, "{}.pkl".format(map_path))

        # # precompute check
        # if os.path.isfile(precomp_path):
        #     # Getting back the objects:
        #     with open(precomp_path, "rb") as f:
        #         self.obj0, self.obj1, self.obj2 = pickle.load(f)
        # else:
        #     # Compute objects to store
        #     self.obj0, self.obj1, self.obj2 = _

        #     # Dump the objects
        #     with open(precomp_path, 'wb') as f:
        #         pickle.dump([self.obj0, self.obj1, self.obj2], f)

        self.rng = rng
        self.logger = logger
        self.maximum_door_frequency = maximum_door_frequency
        self.radius = radius
        self.inner_boundary = [100, 100, 100, 100]
        self.inside_out_state = 0
        self.inside_out_rem = None
        self.inside_out_start_radius = self.radius
        self.rush_in_timer = maximum_door_frequency
        self.rush_in_reverse_timer = maximum_door_frequency
        self.relative_frequencies = np.full((201, 201, 4), -1, dtype=int)
        self.door_timers = np.full((201, 201, 4), 0, dtype=int)
        self.always_closed = np.full((201, 201, 4), False, dtype=bool)
        self.current_relative_pos = [100, 100]
        self.turn_counter = 0

    def move(self, current_percept) -> int:
        """Function which retrieves the current state of the map and returns a movement

            Args:
                current_percept(TimingMazeState): contains current state information
            Returns:
                int: This function returns the next move of the user:
                    WAIT = -1
                    LEFT = 0
                    UP = 1
                    RIGHT = 2
                    DOWN = 3
        """
        self.update_door_timers(current_percept)
        if current_percept.is_end_visible:
            direction = [0, 0, 0, 0]
            reverse_direction = [0, 0, 0, 0]
            for maze_state in current_percept.maze_state:
                if maze_state[0] == 0 and maze_state[1] == 0:
                    direction[maze_state[2]] = maze_state[3]
                if maze_state[0] == 0 and maze_state[1] == 1 and maze_state[2] == constants.UP:
                    reverse_direction[constants.DOWN] = maze_state[3]
                if maze_state[0] == 0 and maze_state[1] == -1 and maze_state[2] == constants.DOWN:
                    reverse_direction[constants.UP] = maze_state[3]
                if maze_state[0] == 1 and maze_state[1] == 0 and maze_state[2] == constants.LEFT:
                    reverse_direction[constants.RIGHT] = maze_state[3]
                if maze_state[0] == -1 and maze_state[1] == 0 and maze_state[2] == constants.RIGHT:
                    reverse_direction[constants.LEFT] = maze_state[3]
            ratio = abs(current_percept.end_x + 0.05)/abs(current_percept.end_x) + abs(current_percept.end_y) + 0.1

            if self.rng.random() < ratio:
                val = self.rush_in_horizontal(current_percept, direction, reverse_direction)
                if val != -1:
                    return val
                val = self.rush_in_vertical(current_percept, direction, reverse_direction)
                if val != -1:
                    return val
                return constants.WAIT
            else:
                val = self.rush_in_vertical(current_percept, direction, reverse_direction)
                if val != -1:
                    return val
                val = self.rush_in_horizontal(current_percept, direction, reverse_direction)
                if val != -1:
                    return val
                return constants.WAIT
        else:
            return self.move_inside_out(current_percept)

    def update_door_timers(self, current_percept):
        door_seen = np.full((201, 201, 4), False, dtype=bool)
        for cell in current_percept.maze_state:
            x, y, direction, state = cell

            # positions relative to start position
            abs_x = x - current_percept.start_x
            abs_y = y - current_percept.start_y
            door_seen[abs_x, abs_y, direction] = True

            # if we see the door on this turn, then increment the timer if the door is closed
            if state == constants.CLOSED:
                self.door_timers[abs_x, abs_y, direction] += 1

            # if the door is closed for more than the maximum frequency, then mark it as always closed
            if self.door_timers[abs_x, abs_y, direction] >= self.maximum_door_frequency:
                self.always_closed[abs_x, abs_y, direction] = True

            #if the door is open, then reset the timer
            if state == constants.OPEN:
                self.door_timers[abs_x, abs_y, direction] = 0

        # for all doors that we were not present in current_percept.maze_state, set the timer as -1
        for i in range(201):
            for j in range(201):
                for k in range(4):
                    if not door_seen[i, j, k]:
                        self.door_timers[i, j, k] = 0


    def rush_in_vertical(self, current_percept, direction, rev_direction) -> int:
        if current_percept.end_y < 0:
            if self.rush_in_timer < 0 or self.rush_in_reverse_timer < 0:
                if direction[constants.RIGHT] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.RIGHT
                if direction[constants.LEFT] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.LEFT
            if direction[constants.UP] == constants.OPEN and rev_direction[constants.UP] == constants.OPEN:
                self.rush_in_timer = self.maximum_door_frequency
                self.rush_in_reverse_timer = self.maximum_door_frequency
                return constants.UP
            if direction[constants.UP] != constants.OPEN:
                self.rush_in_timer -= 1
            if rev_direction[constants.UP] != constants.OPEN:
                self.rush_in_reverse_timer -= 1

        if current_percept.end_y > 0:
            if self.rush_in_timer < 0 or self.rush_in_reverse_timer < 0:
                if direction[constants.RIGHT] == constants.OPEN and rev_direction[constants.RIGHT] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.RIGHT
                if direction[constants.LEFT] == constants.OPEN and rev_direction[constants.LEFT] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.LEFT
            if direction[constants.DOWN] == constants.OPEN and rev_direction[constants.DOWN] == constants.OPEN:
                self.rush_in_timer = self.maximum_door_frequency
                self.rush_in_reverse_timer = self.maximum_door_frequency
                return constants.DOWN
            if direction[constants.DOWN] != constants.OPEN:
                self.rush_in_timer -= 1
            if rev_direction[constants.DOWN] != constants.OPEN:
                self.rush_in_reverse_timer -= 1
        return -1

    def rush_in_horizontal(self, current_percept, direction, rev_direction) -> int:
        if current_percept.end_x > 0:
            if self.rush_in_timer < 0 or self.rush_in_reverse_timer < 0:
                if direction[constants.UP] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.UP
                if direction[constants.DOWN] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.DOWN
            if direction[constants.RIGHT] == constants.OPEN and rev_direction[constants.RIGHT] == constants.OPEN:
                self.rush_in_timer = self.maximum_door_frequency
                self.rush_in_reverse_timer = self.maximum_door_frequency
                return constants.RIGHT
            if direction[constants.RIGHT] != constants.OPEN:
                self.rush_in_timer -= 1
            if rev_direction[constants.RIGHT] != constants.OPEN:
                self.rush_in_reverse_timer -= 1

        if current_percept.end_x < 0:
            if self.rush_in_timer < 0 or self.rush_in_reverse_timer < 0:
                if direction[constants.UP] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.UP
                if direction[constants.DOWN] == constants.OPEN:
                    self.rush_in_timer = self.maximum_door_frequency
                    self.rush_in_reverse_timer = self.maximum_door_frequency
                    return constants.DOWN
            if direction[constants.LEFT] == constants.OPEN and rev_direction[constants.LEFT] == constants.OPEN:
                self.rush_in_timer = self.maximum_door_frequency
                self.rush_in_reverse_timer = self.maximum_door_frequency
                return constants.LEFT
            if direction[constants.LEFT] != constants.OPEN:
                self.rush_in_timer -= 1
            if rev_direction[constants.LEFT] != constants.OPEN:
                self.rush_in_reverse_timer -= 1
        return -1

    def move_inside_out(self, current_percept) -> int:
        # Move towards the boundary but not more than the radius away from the inner boundary
        # if the boundary is less than the radius away, change direction
        direction = [0, 0, 0, 0]
        reverse_direction = [0, 0, 0, 0]
        for maze_state in current_percept.maze_state:
            if maze_state[0] == 0 and maze_state[1] == 0:
                direction[maze_state[2]] = maze_state[3]
            if maze_state[0] == 0 and maze_state[1] == 1 and maze_state[2] == constants.UP:
                reverse_direction[constants.DOWN] = maze_state[3]
            if maze_state[0] == 0 and maze_state[1] == -1 and maze_state[2] == constants.DOWN:
                reverse_direction[constants.UP] = maze_state[3]
            if maze_state[0] == 1 and maze_state[1] == 0 and maze_state[2] == constants.LEFT:
                reverse_direction[constants.RIGHT] = maze_state[3]
            if maze_state[0] == -1 and maze_state[1] == 0 and maze_state[2] == constants.RIGHT:
                reverse_direction[constants.LEFT] = maze_state[3]
        abs_x = - current_percept.start_x
        abs_y = - current_percept.start_y

        if self.inside_out_state == 0:
            self.inside_out_rem = [self.inside_out_start_radius+self.radius, self.inside_out_start_radius+self.radius, self.inside_out_start_radius, self.inside_out_start_radius]
            self.inside_out_start_radius = self.inside_out_start_radius + self.radius
            self.inside_out_state = 1

        if self.inside_out_state == 1:
            if self.inside_out_rem[2] <= 0:
                self.inside_out_state = 2
            else:
                if self.inside_out_rem[2] > 0:
                    if direction[constants.RIGHT] == constants.OPEN and reverse_direction[constants.RIGHT] == constants.OPEN:
                        self.inside_out_rem[2] -= 1
                        return constants.RIGHT

                if ((self.always_closed[abs_x][abs_y][constants.RIGHT] or self.always_closed[abs_x+1][abs_y][constants.LEFT])
                        and direction[constants.DOWN] == constants.OPEN and reverse_direction[constants.DOWN] == constants.OPEN):
                    self.inside_out_rem[3] -= 1
                    return constants.DOWN

                if ((self.always_closed[abs_x][abs_y][constants.RIGHT] or self.always_closed[abs_x+1][abs_y][constants.LEFT])
                        and (self.always_closed[abs_x][abs_y][constants.DOWN] or self.always_closed[abs_x][abs_y+1][constants.UP])
                        and direction[constants.UP] == constants.OPEN and reverse_direction[constants.UP] == constants.OPEN):
                    self.inside_out_rem[1] -= 1
                    return constants.UP

        if self.inside_out_state == 2:
            if self.inside_out_rem[3] <= 0:
                self.inside_out_state = 3
            else:
                if self.inside_out_rem[3] > 0:
                    if direction[constants.DOWN] == constants.OPEN and reverse_direction[constants.DOWN] == constants.OPEN:
                        self.inside_out_rem[3] -= 1
                        return constants.DOWN

                if ((self.always_closed[abs_x][abs_y][constants.DOWN] or self.always_closed[abs_x][abs_y+1][constants.UP])
                        and direction[constants.LEFT] == constants.OPEN and reverse_direction[constants.LEFT] == constants.OPEN):
                    self.inside_out_rem[0] -= 1
                    return constants.LEFT

                if ((self.always_closed[abs_x][abs_y][constants.DOWN] or self.always_closed[abs_x][abs_y+1][constants.UP])
                        and (self.always_closed[abs_x][abs_y][constants.LEFT] or self.always_closed[abs_x-1][abs_y][constants.RIGHT])
                        and direction[constants.RIGHT] == constants.OPEN and reverse_direction[constants.RIGHT] == constants.OPEN):
                    self.inside_out_rem[2] -= 1
                    return constants.RIGHT

        if self.inside_out_state == 3:
            if self.inside_out_rem[0] <= 0:
                self.inside_out_state = 4
            else:
                if self.inside_out_rem[0] > 0:
                    if direction[constants.LEFT] == constants.OPEN and reverse_direction[constants.LEFT] == constants.OPEN:
                        self.inside_out_rem[0] -= 1
                        return constants.LEFT

                if ((self.always_closed[abs_x][abs_y][constants.LEFT] or self.always_closed[abs_x-1][abs_y][constants.RIGHT])
                        and direction[constants.UP] == constants.OPEN and reverse_direction[constants.UP] == constants.OPEN):
                    self.inside_out_rem[1] -= 1
                    return constants.UP

                if ((self.always_closed[abs_x][abs_y][constants.LEFT] or self.always_closed[abs_x-1][abs_y][constants.RIGHT])
                        and (self.always_closed[abs_x][abs_y][constants.UP] or self.always_closed[abs_x][abs_y-1][constants.DOWN])
                        and direction[constants.DOWN] == constants.OPEN and reverse_direction[constants.DOWN] == constants.OPEN):
                    self.inside_out_rem[3] -= 1
                    return constants.DOWN

        if self.inside_out_state == 4:
            if self.inside_out_rem[1] <= 0:
                self.inside_out_state = 0
            else:
                if self.inside_out_rem[1] > 0:
                    if direction[constants.UP] == constants.OPEN and reverse_direction[constants.UP] == constants.OPEN:
                        self.inside_out_rem[1] -= 1
                        return constants.UP

                if ((self.always_closed[abs_x][abs_y][constants.UP] or self.always_closed[abs_x][abs_y-1][constants.DOWN])
                        and direction[constants.RIGHT] == constants.OPEN and reverse_direction[constants.RIGHT] == constants.OPEN):
                    self.inside_out_rem[2] -= 1
                    return constants.RIGHT

                if ((self.always_closed[abs_x][abs_y][constants.UP] or self.always_closed[abs_x][abs_y-1][constants.DOWN])
                        and (self.always_closed[abs_x][abs_y][constants.RIGHT] or self.always_closed[abs_x+1][abs_y][constants.LEFT])
                        and direction[constants.LEFT] == constants.OPEN and reverse_direction[constants.LEFT] == constants.OPEN):
                    self.inside_out_rem[0] -= 1
                    return constants.LEFT

        return constants.WAIT

        def update_relative_frequencies(self, current_percept):
            self.turn_counter += 1 # assuming that update_relative_frequencies is called every time we make a move or wait
            for cell in current_percept.maze_state:
                x, y, direction, state = cell
                abs_x = self.current_relative_pos[0] + x
                abs_y = self.current_relative_pos[1] + y

                # if the door is open
                if state == constants.OPEN:
                    # and it's the first time we are seeing this door (because all rel freq cells are initialized to -1)
                    if self.relative_frequencies[abs_x, abs_y, direction] == -1:
                        self.relative_frequencies[abs_x, abs_y, direction] = self.turn_counter
                    else:
                        # otherwise, if we've seen this cell open before too, take GCD of current turn number and previous frequency estimate
                        # this way, over time, the values will all converge to their precise frequencies
                        self.relative_frequencies[abs_x, abs_y, direction] = math.gcd(self.relative_frequencies[abs_x, abs_y, direction], self.turn_counter)
                # if the door is instead closed
                elif state == constants.CLOSED:
                    # don't do anything
                    pass
                elif state == constants.BOUNDARY:
                    self.relative_frequencies[abs_x, abs_y, direction] = 0

        def update_position(self, move):
            if move == constants.RIGHT:
                self.current_relative_pos[0] += 1
            elif move == constants.LEFT:
                self.current_relative_pos[0] -= 1
            elif move == constants.DOWN:
                self.current_relative_pos[1] += 1
            elif move == constants.UP:
                self.current_relative_pos[1] -= 1