from .navigation import ShortestPathFinder, Node
from .game_state import GameState
from .unit import GameUnit
from .util import debug_write
from typing import List, Tuple, Dict
import queue, sys

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
    def __init__(self, config):
        super().__init__()
        self.config = config
        # cache
        self.end_points_dict = dict()

    def initialize_map(self, game_state: GameState):
        self.initialized = True
        # flags for downstream querying tasks
        self.static_quadrants = []
        # important data structures
        self.game_state = game_state
        self.game_map = self.game_state.game_map
        self.node_map = [[Node() for x in range(self.game_state.ARENA_SIZE)] for y in range(self.game_state.ARENA_SIZE)]
        # fill in walls
        for loc in self.game_map:
            if self.game_state.contains_stationary_unit(loc):
                self.node_map[loc[0]][loc[1]].blocked = True
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
    
    def calc_static_shortest_path(self, 
        start_point: Tuple[int, int], 
        quadrant: int = -1, 
        prev_direction: int = 0) \
        -> List[Tuple[int, int]]:
        # infer quadrant
        if quadrant < 0:
            quadrant = self.infer_quadrant(start_point)
            # debug_write(f"inferred quadrant is: {quadrant}")
        if not quadrant in self.static_quadrants:
            debug_write(f"static shortest path related to q:{quadrant} is not calculated yet")
            return [], 0
        x, y = start_point
        start_node = self.node_map[x][y]
        # this start node cannot reach the edges on the quadrant we specify
        if not start_node.visited.get(quadrant):
            return [], 0
        
        # calculate direction from quadrant
        if quadrant == TOP_RIGHT:
            direction = [1, 1]
        elif quadrant == TOP_LEFT:
            direction = [-1, 1]
        elif quadrant == BOTTOM_LEFT:
            direction = [-1, -1]
        else:
            direction = [1, -1]
        return self._build_path_after_bfs(start_point, quadrant, direction, prev_direction)

    def calc_static_destruct_path(self, start_point: Tuple[int, int], quadrant, prev_direction: int = 0):
        destruct_point = start_point
        best_idealness = self._get_idealness(start_point, quadrant)
        current = queue.Queue()
        # dict holding visited node
        visited = set()
        # enforce it as a tuple, not list (so it's hashable)
        start_point = tuple(start_point)
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
        
        # backward BFS from destruct point
        current = queue.Queue()
        tmp_quadrant = 4
        for nodes in self.node_map:
            for node in nodes:
                if tmp_quadrant in node.visited:
                    del node.visited[tmp_quadrant]

        self.node_map[destruct_point[0]][destruct_point[1]].dist[tmp_quadrant] = 0
        self.node_map[destruct_point[0]][destruct_point[1]].visited[tmp_quadrant] = True
        current.put(destruct_point)

        while not current.empty():
            current_loc = current.get()
            current_node = self.node_map[current_loc[0]][current_loc[1]]
            for neighbor in self._get_neighbors(current_loc):
                if not self.game_map.in_arena_bounds(neighbor) or self.node_map[neighbor[0]][neighbor[1]].blocked:
                    continue

                neighbor_node = self.node_map[neighbor[0]][neighbor[1]]
                if not neighbor_node.visited.get(tmp_quadrant) and not current_node.blocked:
                    neighbor_node.dist[tmp_quadrant] = current_node.dist[tmp_quadrant] + 1
                    neighbor_node.visited[tmp_quadrant] = True
                    current.put(neighbor)

        # calculate direction from quadrant
        if quadrant == TOP_RIGHT:
            direction = [1, 1]
        elif quadrant == TOP_LEFT:
            direction = [-1, 1]
        elif quadrant == BOTTOM_LEFT:
            direction = [-1, -1]
        else:
            direction = [1, -1]
        return self._build_path_after_bfs(start_point, tmp_quadrant, direction, prev_direction)
    
    def _build_path_after_bfs(self, start_point, quadrant, direction, prev_direction):
        path = [start_point]
        current = start_point
        # default move direction is 
        move_direction = prev_direction

        while not self.node_map[current[0]][current[1]].dist[quadrant] == 0:
            next_move = self._choose_next_move(current, move_direction, direction, quadrant)

            if current[0] == next_move[0]:
                move_direction = self.VERTICAL
            else:
                move_direction = self.HORIZONTAL
            path.append(next_move)
            current = next_move
        return path, move_direction

    def _get_idealness(self, point, quadrant):
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
            current_dist = self.node_map[x][y].dist.get(quadrant, sys.maxsize)

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

    """
    Below are the core codes for dynamic path finding - which involves complicated
    game logic simulation and should be written & checked carefully
    """
    def calc_dynamic_shortest_path(self, 
        start_point: Tuple[int, int], 
        game_units: List[GameUnit], 
        quantities: List[int],
        quadrant: int = -1,
        player_index: int = 0):
        """
        Args:
            - start_point: location of the starting point for the search, should usually on an edge
            - game_units (List[GameUnit] || GameUnit): a list of game units that represent the types
              if provided a single GameUnit, will cast it into a list
            - quantities (List[int] || int): a list of quantities for each game unit in game_units
            - quadrant (Optional[int]): the target edge that we want to reach; can be inferred from 
              start point automatically
            - player_index (Optional[int]): indicate you want to simulate as your side or enemy side
        Returns:
            - dynamic_path (List[Tuple[int, int]]): the location trajectory from start to a target edge,
              or a self destruction point, or some point where all units got killed
            - success (bool): true if it reaches the desired location (an edge or self destruction loc),
              false if the units all get killed before reaching
            - remain_quantities (List[int]): similar to `quantities` above
            - destroyed (List[GameUnit]): the list of enemy structures getting destroyed in this process
            - structure_map (Dict[GameUnit, int]): the health for enemy structures that have been attacked 
              at least once. Can be seen as a superset of `destroyed`.
            - bomb (bool): whether the units have self destructed
        """
        # handle single unit input case
        if isinstance(game_units, GameUnit):
            game_units = [game_units]
            quantities = [quantities]
        # error checking with inputs
        assert len(game_units) < 3 and len(quantities) < 3 and len(game_units) == len(quantities)
        
        # infer quadrant
        if quadrant < 0:
            quadrant = self.infer_quadrant(start_point)
            # debug_write("infered quadrant", quadrant)
        if not quadrant in self.static_quadrants:
            debug_write(f"static shortest path related to q:{quadrant} is not calculated yet")
            return []

        static_path, last_direction = self.calc_static_shortest_path(start_point)
        if not static_path:
            static_path, last_direction = self.calc_static_destruct_path(start_point, quadrant)
        
        old_loc = game_units[0].x, game_units[0].y
        game_units[0].x, game_units[0].y = start_point
        # this is just some num > 4 to be used for indexing in nodes
        tmp_quadrant = 5

        # loading core data
        old_quantities = quantities.copy()
        min_health_idx = 0
        unit_health = []
        if len(game_units) == 2:
            if game_units[0].health < game_units[1].health:
                unit_health = [game_units[1].health] * quantities[1] + [game_units[0].health] * quantities[0]
            else:
                unit_health = [game_units[0].health] * quantities[0] + [game_units[1].health] * quantities[1]
                min_health_idx = 1
        else:
            unit_health = [game_units[0].health] * quantities[0]

        unit_damage = [unit.damage_f for unit in game_units]
        unit_speed = int(1 / game_units[0].speed) # expressed as # frame for a step

        i = 0
        curr_loc = static_path[i]
        dynamic_path = [curr_loc]

        shield_list: List[GameUnit] = []
        attacked_map: Dict[GameUnit, int] = {}
        destroyed_list: List[GameUnit] = []
        for loc in self.game_map:
            x, y = loc
            self.node_map[x][y].dist[tmp_quadrant] = self.node_map[x][y].dist.get(quadrant, sys.maxsize)
            self.node_map[x][y].visited[tmp_quadrant] = self.node_map[x][y].visited.get(quadrant, False)
            if self.game_state.contains_stationary_unit(loc):
                loc_unit: GameUnit = self.game_map[loc][0]
                # finding supports
                if loc_unit.unit_type == "EF" and loc_unit.player_index == player_index:
                    shield_list.append(loc_unit)

        # safe check that handles cases like (1, 2) == [1, 2]
        while i != len(static_path):
            # receive shield
            new_shield_list = []
            new_destroyed_list = []
            for shield_unit in shield_list:
                shield_loc = (shield_unit.x, shield_unit.y)
                if self.game_map.distance_between_locations(curr_loc, shield_loc) < shield_unit.shieldRange:
                    new_shield = shield_unit.shieldPerUnit + shield_unit.shieldBonusPerY * shield_unit.y
                    for i in range(len(unit_health)):
                        unit_health[i] += new_shield
                else:
                    new_shield_list.append(shield_unit)
            shield_list = new_shield_list 
            # find attacked
            enemy_attacked: GameUnit = self.game_state.get_target(game_units[0])
            if enemy_attacked and enemy_attacked not in attacked_map:
                attacked_map[enemy_attacked] = enemy_attacked.health
            attacked_health = attacked_map.get(enemy_attacked, 0)
            # find attacker
            enemy_attackers: List[GameUnit] = self.game_state.get_attackers(curr_loc, player_index)
            for _ in range(unit_speed):
                # this is calculated before attacking/attacked
                total_damage = sum([unit_damage[i] * quantities[i] for i in range(len(unit_damage))])
                # simulate being attacked by enemy
                for attacker in enemy_attackers:
                    damage = attacker.damage_i
                    if not len(unit_health):
                        continue
                    u_health = unit_health.pop()
                    if damage >= u_health:
                        # used to determine which unit type is eliminated
                        if len(unit_health) <= old_quantities[min_health_idx]:
                            quantities[min_health_idx] -= 1
                        else:
                            quantities[1 - min_health_idx] -= 1
                    else:
                        unit_health.append(u_health - damage)
                # simulate attacking some enemies
                while total_damage > 0 and enemy_attacked:
                    reduced_health = min(attacked_health, total_damage)
                    total_damage -= reduced_health
                    attacked_health -= reduced_health

                    if not attacked_health: # == 0
                        if enemy_attacked in enemy_attackers:
                            enemy_attackers.remove(enemy_attacked)
                        # below are dangerous codes, be careful in editing
                        rx, ry = enemy_attacked.x, enemy_attacked.y
                        # temporary remove the blocked status
                        self.node_map[rx][ry].blocked = False
                        # need to change the game map directly as well
                        self.game_map[rx, ry] = []
                        # and record this point for later restoration
                        new_destroyed_list.append(enemy_attacked)
                        attacked_map[enemy_attacked] = 0
                        enemy_attacked = self.game_state.get_target(game_units[0])
                        if enemy_attacked and enemy_attacked not in attacked_map:
                            attacked_map[enemy_attacked] = enemy_attacked.health
                        attacked_health = attacked_map.get(enemy_attacked, 0)
                    else:
                        attacked_map[enemy_attacked] = attacked_health
                
                if not len(unit_health): # failed
                    # restoration phase
                    self._restore_destroyed(destroyed_list)
                    game_units[0].x, game_units[0].y = old_loc
                    return {
                        "dynamic_path": dynamic_path,
                        "success": False,
                        "remain_quantities": [0],
                        "destroyed": destroyed_list,
                        "structure_map": attacked_map,
                        "bombed": False
                    }

            # simulate editing the shortest path
            i += 1
            if i == len(static_path):
                continue 

            if new_destroyed_list:
                self._partial_update_shortest_path(new_destroyed_list, quadrant=quadrant)
                new_static_path, last_direction = self.calc_static_shortest_path(curr_loc, tmp_quadrant, last_direction)
                if not new_static_path:
                    new_static_path, last_direction = self.calc_static_destruct_path(curr_loc, tmp_quadrant, last_direction)
                static_path[i:] = new_static_path[1:]
                destroyed_list.extend(new_destroyed_list)

            # simulate stepping one step forward
            curr_loc = static_path[i]
            dynamic_path.append(curr_loc)
            game_units[0].x, game_units[0].y = curr_loc

        # judge whether it reaches an edge or self-destructed
        bomb = list(dynamic_path[-1]) not in self.end_points_dict.get(quadrant, [])
        if bomb:
            steps = len(dynamic_path) - 1
            for i, unit in enumerate(game_units):
                bomb_d = unit.destruct_damage * quantities[i]
                bomb_s = unit.destruct_min_steps
                if not bomb_d or bomb_s > steps:
                    continue
                bomb_r = unit.destruct_radius
                # calculating bombing damage
                possible_loc = self.game_map.get_locations_in_range(dynamic_path[-1], bomb_r)
                for loc in possible_loc:
                    if self.game_map[loc] and self.game_map[loc][0].stationary:
                        enemy_attacked = self.game_map[loc][0]
                        if enemy_attacked not in attacked_map:
                            attacked_map[enemy_attacked] = enemy_attacked.health
                        if attacked_map[enemy_attacked] <= bomb_d and enemy_attacked not in destroyed_list:
                            destroyed_list.append(enemy_attacked)

        # restoration phase
        self._restore_destroyed(destroyed_list)
        game_units[0].x, game_units[0].y = old_loc

        return {
            "dynamic_path": dynamic_path,
            "success": True,
            "remain_quantities": quantities,
            "destroyed": destroyed_list,
            "structure_map": attacked_map,
            "bombed": bomb
        }

    def _partial_update_shortest_path(self, destroyed_units: List[GameUnit], quadrant: int, tmp_quadrant: int = 5):
        """
        Instead of redoing an entire BFS, we focus on the destroyed units only
        """
        affected_locs = [(unit.x, unit.y) for unit in destroyed_units]
        end_points = self.end_points_dict[quadrant]
        for loc in affected_locs:
            current = queue.Queue()
            if list(loc) in end_points: # if the unblocked place is destination
                curr_node = self.node_map[loc[0]][loc[1]]
                curr_node.visited[tmp_quadrant] = True
                curr_node.dist[tmp_quadrant] = 0
            else:
                neighbors = self._get_neighbors(loc)
                min_dist = sys.maxsize
                for neighbor in neighbors:
                    if not self.game_map.in_arena_bounds(neighbor):
                        continue
                    neighbor_node = self.node_map[neighbor[0]][neighbor[1]]
                    if not neighbor_node.blocked and neighbor_node.visited[tmp_quadrant] and neighbor_node.dist[tmp_quadrant] < min_dist:
                        min_dist = neighbor_node.dist[tmp_quadrant]
                if min_dist < sys.maxsize:
                    curr_node = self.node_map[loc[0]][loc[1]]
                    curr_node.visited[tmp_quadrant] = True
                    curr_node.dist[tmp_quadrant] = min_dist + 1
            current.put(loc)

            while not current.empty():
                curr_loc = current.get()
                curr_node = self.node_map[curr_loc[0]][curr_loc[1]]
                for neighbor in self._get_neighbors(curr_loc):
                    if not self.game_map.in_arena_bounds(neighbor) or self.node_map[neighbor[0]][neighbor[1]].blocked:
                        continue
                    
                    neighbor_node = self.node_map[neighbor[0]][neighbor[1]]
                    new_dist = curr_node.dist[tmp_quadrant] + 1
                    if not neighbor_node.visited.get(tmp_quadrant):            
                        neighbor_node.dist[tmp_quadrant] = new_dist
                        neighbor_node.visited[tmp_quadrant] = True
                        current.put(neighbor)
                    elif new_dist < neighbor_node.dist[tmp_quadrant]:
                        neighbor_node.dist[tmp_quadrant] = new_dist
                        current.put(neighbor)

        self.static_quadrants.append(tmp_quadrant)
    
    def _restore_destroyed(self, destroyed_list: List[GameUnit]):
        for unit in destroyed_list:
            assert unit.stationary
            self.node_map[unit.x][unit.y].blocked = True
            self.game_map[unit.x, unit.y] = [unit]
