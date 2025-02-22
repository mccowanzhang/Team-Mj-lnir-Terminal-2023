import itertools

import gamelib
import math

class Strategy():
    def __init__(self, config, EDGES=None, tiles=None):
        """
        init
        """
        super().__init__()
        # directions for deciding where to focus defense/offense
        self.LEFT = 0
        self.CENTRE = 1
        self.RIGHT = 2
        # which side to defend, weighting on where we think they will attack to decide which defenses we allocate
        self.defend_left = 10
        self.defend_centre = 10
        self.defend_right = 10
        # direction for attack
        self.attack_direction = 0
        self.EDGES = EDGES
        self.tiles = tiles
        # gamelib.debug_write("passed in: " + str(self.EDGES))
        # gamelib.debug_write("strategy: " + str(self.EDGES))

        # global variables
        self.config = config
        self.path_finder = gamelib.CustomPathFinder(self.config)
        self.reachable_map = []
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

    def static_map(self, game_state, path_finder):
        list_of_paths = []
        # gamelib.debug_write(self.EDGES)
        valid_spawns = [[x, y] for [x, y] in (self.EDGES[0] + self.EDGES[1]) if not self.tiles[28 * y + x].unit]
        for spawn in valid_spawns:
            paths, _ = path_finder.calc_static_shortest_path(spawn)
            list_of_paths.append(paths)

        self.reachable_map = [list(filter(None, x)) for x in list((itertools.zip_longest(*list_of_paths, fillvalue=[])))]
        # gamelib.debug_write(self.reachable_map)

    def calc_delays(self):
        left_tower_kill = False
        right_tower_kill = False

        target_step = 1
        new_list = list(self.reachable_map.copy())
        while target_step < 6 and target_step * 4 - 1 < len(new_list) and len(new_list[target_step * 4 - 1]) > 0:
            sub_list = new_list[target_step * 4 - 1]
            location = 0
            slist_len = len(sub_list)
            while location < slist_len:
                kill = False
                if not sub_list[location]:
                    kill = True
                elif sub_list[location][1] <= 18:
                    if sub_list[location][0] <= 11:
                        left_tower_kill = True
                        kill = True
                    if sub_list[location][1] >= 16:
                        right_tower_kill = True
                        kill = True

                if kill:
                    for s_lists in new_list:
                        if location < len(s_lists):
                            s_lists.pop(location)

                    location -= 1
                    slist_len -= 1
                location += 1

            target_step += 2

        return target_step, left_tower_kill, right_tower_kill

    def play_turn(self, game_state: gamelib.GameState, scored_on_locations, tiles, mp_used):
        """
        decision making
        """
       # analyze map to update strategy 
        self.path_finder.initialize_map(game_state)
        self.path_finder.prep_static_shortest_path()
        self.static_map(game_state, self.path_finder)

        defense_turn = False
        total = sum(mp_used)
        average = total // len(mp_used)
        attacks = []
        enemy_mp = game_state.get_resource(game_state.MP, 1)
        for used in mp_used:
            if used >= average + 2:
                attacks.append(used)
        if len(attacks) > 2:
            defense_turn = enemy_mp >= (sum(attacks) // len(attacks)) - 2 or enemy_mp > game_state.my_health + 2
        else: 
            defense_turn = enemy_mp >= 8

        if defense_turn:
            num_bombs = min(1 + game_state.turn_number // 30, 2)
            if game_state.turn_number > 10:
                analysis = self.calc_delays()
                if analysis[1]:
                    if analysis[0] > 3:
                        self.deploy_five_chamber(game_state, self.LEFT, num_bombs)
                    self.deploy_three_chamber(game_state, self.LEFT, num_bombs)
                if analysis[2]:
                    if analysis[0] > 3:
                        self.deploy_five_chamber(game_state, self.RIGHT, num_bombs)
                    self.deploy_three_chamber(game_state, self.RIGHT, num_bombs)
            else: 
                self.deploy_three_chamber(game_state, self.RIGHT, num_bombs)
                self.deploy_three_chamber(game_state, self.LEFT, num_bombs)

        if len(scored_on_locations) > 0:
            x = scored_on_locations[len(scored_on_locations) - 1][0]
            reinforce_side = self.LEFT 
            if x < self.DEFEND_LEFT_THRESHOLD:
                reinforce_side = self.LEFT
            elif x > self.DEFEND_RIGHT_THRESHOLD:
                reinforce_side = self.RIGHT
            else:
                reinforce_side = self.CENTRE
            self.reactive_defense(game_state, reinforce_side)
        else:
            self.build_up_base(game_state)  
        

        # TO REPLACE analyze if we can send a strong enough attack 
        # and what number of each unit
        total_mp = math.floor(game_state.get_resource(game_state.MP))
        # attack_combinations = [[total_mp -2 ,0], [0, (total_mp - 2) // 3], [min(total_mp - (total_mp - 2) // 3,0),(total_mp - 2) // 3]]
        # best_attack = {"num_scouts":0, "num_demolisher": 0, "location": [6,7], "score": 0, "ends_game": False}
       
        # units = [gamelib.GameUnit(SCOUT, self.config, 0, None), 
        #         gamelib.GameUnit(DEMOLISHER, self.config, 0, None)]
        # for combo in attack_combinations:
        #     for location in self.attack_locations:
        #         attack = path_finder.calc_dynamic_shortest_path(location, units, combo)
        #         damage = sum(attack["remain_quantities"])
        #         score = damage * 3
        #         ends_game = damage > game_state.enemy_health + 1
        #         for building in attack["destroyed"]:
        #             # score += building.cost
        #             gamelib.debug_write("bulding: {}".format(building))
        #         if score > best_attack["score"] and (not best_attack["ends_game"] or ends_game):
        #             best_attack = {"num_scouts": combo[0], "num_demolisher": combo[1], "location": location, "score": score, "ends_game": ends_game}
        #             gamelib.debug_write("path: {} success: {} remain_quantities: {}, destroyed: {}, bombed: {}".format(attack["dynamic_path"], attack["success"], attack["remain_quantities"], attack["destroyed"], attack["bombed"]))
        
        # gamelib.debug_write("({},{}) scouts: {}, demolishers: {}, damage: {}".format(best_attack["location"][0], best_attack["location"][1], best_attack["num_scouts"],best_attack["num_demolisher"], best_attack["damage"]))
        # attack_turn = best_attack["score"] > game_state.turn_number // 10 + 5 or best_attack["ends_game"]

        left_defense = 0
        right_defense = 0
        for tile in tiles:
            if tile.x <= 13:
                left_defense += tile.enemy_coverage
            else:
                right_defense += tile.enemy_coverage
        num_scouts = 2
        num_demolishers = min(2 + game_state.turn_number // 18, 5)
        best_attack = {"num_scouts": num_scouts, "num_demolisher": num_demolishers, "location": [13,0] if left_defense >= right_defense else [14,0], "damage": 0}
        if total_mp > num_scouts + (num_demolishers * 3) + 2:
        # if attack_turn:
            # gamelib.debug_write("num scouts: {} num demolish: {} location: {} score {} ends game {}".format(best_attack["num_scouts"], best_attack["num_demolisher"], best_attack["location"], best_attack["score"], best_attack["ends_game"]))
            self.reactive_offense(game_state, best_attack["num_scouts"], best_attack["num_demolisher"], best_attack["location"])

        # how we spend struct points
        extra_struct_points = True
        if extra_struct_points:
            self.build_up_base(game_state)
    
    def round_one(self, game_state):
        interceptor_locations = [[3,10],[24,10],[8,5],[19,5]]
        game_state.attempt_spawn(INTERCEPTOR, interceptor_locations)
                        
    def reactive_defense(self, game_state, reinforce_side):
        """
        plays defenses
        """
        # build up base
        if reinforce_side == self.LEFT:
            for location in self.l_turret_locations:
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)

            for location in self.l_upgraded_wall_locations:
                game_state.attempt_spawn(WALL, location)
                game_state.attempt_upgrade(location)

            for location in self.l_defense_wall_locations:
                game_state.attempt_spawn(WALL, location)
                game_state.attempt_upgrade(location)

            game_state.attempt_spawn(WALL, self.l_chamber_wall_locations)
            game_state.attempt_spawn(WALL, self.l_navigation_wall_locations)
            game_state.attempt_upgrade(self.l_defense_wall_locations)
            game_state.attempt_upgrade(self.l_chamber_wall_locations)

                    # build up supports
            for location in self.upgraded_support_locations:
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)

            for location in self.l_extra_turret_locations:
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)

            game_state.attempt_upgrade(self.l_navigation_wall_locations)

            for location in self.extra_extra_support_locations:
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)
        elif reinforce_side == self.CENTRE:
            for location in self.c_turret_locations:
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)

            game_state.attempt_spawn(WALL, self.r_chamber_wall_locations)
            game_state.attempt_spawn(WALL, self.l_chamber_wall_locations)
            game_state.attempt_spawn(WALL, self.r_navigation_wall_locations)
            game_state.attempt_spawn(WALL, self.l_navigation_wall_locations)
            game_state.attempt_upgrade(self.r_defense_wall_locations)
            game_state.attempt_upgrade(self.l_defense_wall_locations)
            game_state.attempt_upgrade(self.r_chamber_wall_locations)
            game_state.attempt_upgrade(self.l_chamber_wall_locations)


                    # build up supports
            for location in self.upgraded_support_locations:
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)

            for location in self.c_extra_turret_locations:
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)

            game_state.attempt_upgrade(self.l_navigation_wall_locations)
            game_state.attempt_upgrade(self.r_navigation_wall_locations)

            for location in self.extra_extra_support_locations:
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)
        else:
            for location in self.r_turret_locations:
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)

            for location in self.r_upgraded_wall_locations:
                game_state.attempt_spawn(WALL, location)
                game_state.attempt_upgrade(location)

            for location in self.r_defense_wall_locations:
                game_state.attempt_spawn(WALL, location)
                game_state.attempt_upgrade(location)

            game_state.attempt_spawn(WALL, self.r_chamber_wall_locations)
            game_state.attempt_spawn(WALL, self.r_navigation_wall_locations)
            game_state.attempt_upgrade(self.r_defense_wall_locations)
            game_state.attempt_upgrade(self.r_chamber_wall_locations)

                    # build up supports
            for location in self.upgraded_support_locations:
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)

            for location in self.r_extra_turret_locations:
                game_state.attempt_spawn(TURRET, location)
                game_state.attempt_upgrade(location)

            game_state.attempt_upgrade(self.r_navigation_wall_locations)

            for location in self.extra_extra_support_locations:
                game_state.attempt_spawn(SUPPORT, location)
                game_state.attempt_upgrade(location)
        

    def reactive_offense(self, game_state, num_scouts, num_demolishers, location=[6,7]):
        """
        plays offense
        """
        game_state.attempt_spawn(DEMOLISHER, location, num_demolishers)
        game_state.attempt_spawn(SCOUT, location, num_scouts)

        game_state.attempt_spawn(INTERCEPTOR, self.l_one_chamber_locations)
        game_state.attempt_spawn(INTERCEPTOR, self.r_one_chamber_locations)

    def build_up_base(self, game_state):

        # repair initial base
        for l, c, r in zip(self.l_turret_locations, self.c_turret_locations, self.r_turret_locations):
            game_state.attempt_spawn(TURRET, l)
            game_state.attempt_spawn(TURRET, c)
            game_state.attempt_spawn(TURRET, r)
            game_state.attempt_upgrade(l)
            game_state.attempt_upgrade(c)
            game_state.attempt_upgrade(r)

        for l, r in zip(self.l_upgraded_wall_locations, self.r_upgraded_wall_locations):
            game_state.attempt_spawn(WALL, l)
            game_state.attempt_upgrade(l)
            game_state.attempt_spawn(WALL, r)
            game_state.attempt_upgrade(r)

        for l, r in zip(self.l_defense_wall_locations, self.r_defense_wall_locations):
            game_state.attempt_spawn(WALL, l)
            game_state.attempt_spawn(WALL, r)
            game_state.attempt_upgrade(l)
            game_state.attempt_upgrade(r)

        game_state.attempt_spawn(WALL, self.l_chamber_wall_locations)
        game_state.attempt_spawn(WALL, self.r_chamber_wall_locations)
        game_state.attempt_spawn(WALL, self.l_navigation_wall_locations)
        game_state.attempt_spawn(WALL, self.r_navigation_wall_locations)

        # build up supports
        for location in zip(self.upgraded_support_locations):
            game_state.attempt_spawn(SUPPORT, location)
            game_state.attempt_upgrade(location)

        # fortify defenses 
        for l, c, r in zip(self.l_extra_turret_locations, self.c_extra_turret_locations, self.r_extra_turret_locations):
            game_state.attempt_spawn(TURRET, l)
            game_state.attempt_spawn(TURRET, c)
            game_state.attempt_spawn(TURRET, r)
            game_state.attempt_upgrade(l)
            game_state.attempt_upgrade(c)
            game_state.attempt_upgrade(r)

        for l, r in zip(self.l_chamber_wall_locations, self.r_chamber_wall_locations):
            game_state.attempt_upgrade(l)
            game_state.attempt_upgrade(r)

        for l, r in zip(self.l_navigation_wall_locations, self.r_navigation_wall_locations):
            game_state.attempt_upgrade(l)
            game_state.attempt_upgrade(r)

        for location in self.extra_extra_support_locations:
            game_state.attempt_spawn(SUPPORT, location)
            game_state.attempt_upgrade(location)

