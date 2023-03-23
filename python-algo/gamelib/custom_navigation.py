from .navigation import ShortestPathFinder, Node
from .game_state import GameState
from .util import debug_write
from typing import List, Tuple
import queue

# constants
TOP_RIGHT = 0
TOP_LEFT = 1
BOTTOM_LEFT = 2
BOTTOM_RIGHT = 3

class Node:
    """An optimized pathfinding node"""
    def __init__(self):
        self.blocked = False
        # a dictionary of quadrant: distance pairs indicating shortest distance to each edge
        # a dictionary of visited: similar as above
        self.dist = dict()
        self.visited = dict()

class CustomPathFinder(ShortestPathFinder):
    def __init__(self):
        super().__init__()
        # cache
        self.end_points_dict = dict()

    def initialize_map(self, game_state: GameState):
        self.initialized = True
        # flags for downstream querying tasks
        self.static_quadrants = []
        self.dynamic_ready = False
        # important data structures
        self.game_state = game_state
        self.game_map = self.game_state.game_map
        self.node_map = [[Node() for x in range(self.game_state.ARENA_SIZE)] for y in range(self.game_state.ARENA_SIZE)]
        # caching self destruct locations
        self.destruct_map = {i : {} for i in range(4)}

    def prep_static_shortest_path(self, quadrants: List[int] = [0, 1]):
        if not self.initialized:
            debug_write("cannot calculate on an uninitialized pathfinder")
            return 

        for quadrant in quadrants:
            if quadrant not in self.end_points_dict:
                self.end_points_dict[quadrant] = self.game_map.get_edge_locations(quadrant)
            end_points = self.end_points_dict[quadrant]
            debug_write(end_points)
        
            current = queue.Queue()
            for ep in end_points:
                self.node_map[ep[0]][ep[1]].dist[quadrant] = 0
                self.node_map[ep[0]][ep[1]].visited[quadrant] = True
                current.put(ep)

            #While current is not empty
            while not current.empty():
                current_loc = current.get()
                current_node = self.node_map[current_loc[0]][current_loc[1]]
                for neighbor in self._get_neighbors(current_loc):
                    if not self.game_map.in_arena_bounds(neighbor) or self.node_map[neighbor[0]][neighbor[1]].blocked:
                        continue

                    neighbor_node = self.node_map[neighbor[0]][neighbor[1]]
                    if not neighbor_node.visited.get(quadrant) and not current_node.blocked:
                        neighbor_node.dist[quadrant] = current_node.dist[quadrant] + 1
                        neighbor_node.visited[quadrant] = True
                        current.put(neighbor)

            self.static_quadrants.append(quadrant)
    
    def calc_static_shortest_path(self, start_point: Tuple[int, int], quadrant: int = -1) \
        -> List[Tuple[int, int]]:
        # infer quadrant
        if quadrant < 0:
            quadrant = self.infer_quadrant(start_point)
            debug_write(f"inferred quadrant is: {quadrant}")
        if not quadrant in self.static_quadrants:
            debug_write(f"shortest path related to q:{quadrant} is not calculated yet")
            return []
        x, y = start_point
        start_node = self.node_map[x][y]
        # this start node cannot reach the edges on the quadrant we specify
        if not start_node.visited[quadrant]:
            return []
        
        # actual construction work done here!
        path = [start_point]
        current = start_point
        # default move direction is 
        move_direction = 0
        # calculate direction from quadrant
        if quadrant == TOP_RIGHT:
            direction = [1, 1]
        elif quadrant == TOP_LEFT:
            direction = [-1, 1]
        elif quadrant == BOTTOM_LEFT:
            direction = [-1, -1]
        else:
            direction = [1, -1]

        while not self.node_map[current[0]][current[1]].dist[quadrant] == 0:
            next_move = self._choose_next_move(current, move_direction, direction, quadrant)

            if current[0] == next_move[0]:
                move_direction = self.VERTICAL
            else:
                move_direction = self.HORIZONTAL
            path.append(next_move)
            current = next_move
        return path

    def calc_static_destruct_point(self, start_point: Tuple[int, int], quadrant):
        # use cache if possible
        if start_point in self.destruct_map[quadrant]:
            return self.destruct_map[quadrant][start_point]

        destruct_point = start_point
        best_idealness = self._get_idealness(start_point, quadrant)
        current = queue.Queue()
        # dict holding visited node
        visited = set()
        current.put(start_point)
        visited.add(start_point)
        while not current.empty():
            current_loc = current.get()
            for neighbor in self._get_neighbors(current_loc):
                if not self.game_map.in_arena_bounds(neighbor) or self.node_map[neighbor[0]][neighbor[1]].blocked:
                    continue
                
                new_idealness = self._get_idealness(neighbor, quadrant)
                if new_idealness > best_idealness:
                    best_idealness = new_idealness
                    destruct_point = neighbor

                if not neighbor in visited:
                    visited.add(neighbor)
                    current.put(neighbor)

        # cache the BFS above
        self.destruct_map[quadrant][start_point] = destruct_point 
        return destruct_point

    def _get_idealness(point, quadrant):
        idealness = 0
        if quadrant in [0, 1]:
            idealness += 28 * point[1]
        else: 
            idealness += 28 * (27 - point[1])
        if quadrant in [0, 3]:
            idealness += point[0]
        else: 
            idealness += (27 - point[0])
        return idealness

    def _choose_next_move(self, current_point, previous_move_direction, direction, quadrant):
        """
        Given the current location and adjacent locations, return the best 'next step' for a given unit to take
        """
        neighbors = self._get_neighbors(current_point)

        ideal_neighbor = current_point
        best_dist = self.node_map[current_point[0]][current_point[1]].dist[quadrant]
        for neighbor in neighbors:
            if not self.game_map.in_arena_bounds(neighbor) or self.node_map[neighbor[0]][neighbor[1]].blocked:
                continue

            new_best = False
            x, y = neighbor
            current_dist = self.node_map[x][y].dist[quadrant]

            #Filter by pathlength
            if current_dist > best_dist:
                continue 
            elif current_dist < best_dist:
                new_best = True

            #Filter by direction based on prev move
            if new_best or self._better_direction(current_point, neighbor, ideal_neighbor, previous_move_direction, direction):
                ideal_neighbor = neighbor
                best_dist = current_dist

        return ideal_neighbor

    def _better_direction(self, prev_tile, new_tile, prev_best, previous_move_direction, direction):
        """Compare two tiles and return True if the unit would rather move to the new one

        """
        #True if we are moving in a different direction than prev move and prev is not
        #If we previously moved horizontal, and now one of our options has a different x position then the other (the two options are not up/down)
        if previous_move_direction == self.HORIZONTAL and not new_tile[0] == prev_best[0]:
            #We want to go up now. If we have not changed our y, we are not going up
            if prev_tile[1] == new_tile[1]:
                return False 
            return True
        if previous_move_direction == self.VERTICAL and not new_tile[1] == prev_best[1]:
            if prev_tile[0] == new_tile[0]:
                #debug_write("contender {} has the same x coord as prev tile {} so we will keep best move {}".format(new_tile, prev_tile, prev_best))
                return False
            return True
        # in the case of newly deployed unit, prefer a verticle movement
        if previous_move_direction == 0: 
            if prev_tile[1] == new_tile[1]: 
                return False
            return True
        
        #To make it here, both moves are on the same axis 
        if new_tile[1] == prev_best[1]: #If they both moved horizontal...
            if direction[0] == 1 and new_tile[0] > prev_best[0]: #If we moved right and right is our direction, we moved towards our direction
                return True 
            if direction[0] == -1 and new_tile[0] < prev_best[0]: #If we moved left and left is our direction, we moved towards our direction
                return True 
            return False 
        if new_tile[0] == prev_best[0]: #If they both moved vertical...
            if direction[1] == 1 and new_tile[1] > prev_best[1]: #If we moved up and up is our direction, we moved towards our direction
                return True
            if direction[1] == -1 and new_tile[1] < prev_best[1]: #If we moved down and down is our direction, we moved towards our direction
                return True
            return False
        return True
    
    def infer_quadrant(self, point: Tuple[int, int]):
        assert self.game_map.in_arena_bounds(point)
        x, y = point
        boundary = self.game_state.HALF_ARENA
        if x < boundary:
            if y < boundary:
                return 0
            else:
                return 3
        else:
            if y < boundary:
                return 1
            else:
                return 2