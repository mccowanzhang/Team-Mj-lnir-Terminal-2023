import gamelib
import math

class Strategy():
    def __init__(self, config):
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

        # global variables
        self.config = config 
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

    def play_turn(self, game_state, scored_on_locations):
        """
        decision making
        """
        # analyze map to update strategy 
        if len(scored_on_locations) > 0:
            x = scored_on_locations[len(scored_on_locations) - 1][0]
            reinforce_side = self.LEFT 
            if x < 8:
                reinforce_side = self.LEFT
            elif x <= 20:
                reinforce_side = self.CENTRE
            else:
                reinforce_side = self.RIGHT
            self.reactive_defense(game_state, reinforce_side)
        else:
            self.build_up_base(game_state)  
        defense_turn = game_state.get_resource(game_state.MP, 1) > 10
        if defense_turn:
            self.bombs(game_state, self.RIGHT)
            self.bombs(game_state, self.LEFT)

        # TO REPLACE analyze if we can send a strong enough attack 
        # and what number of each unit
        total_mp = math.floor(game_state.get_resource(game_state.MP))
        attack_combinations = [[num_scouts, num_demolishers] 
                               for num_scouts in range(total_mp - 1) 
                               for num_demolishers in range(total_mp - 1) 
                               if num_scouts + num_demolishers * 3 <= total_mp - 2]
        best_attack = {"num_scouts":0, "num_demolisher": 0, "location": [6,7], "damage": 0}
        path_finder = gamelib.CustomPathFinder(self.config)
        path_finder.initialize_map(game_state)
        path_finder.prep_static_shortest_path()
        for combo in attack_combinations:
            for location in self.attack_locations:
                units = [gamelib.GameUnit(SCOUT, self.config, 0, 5, location[0], location[1]), 
                        gamelib.GameUnit(DEMOLISHER, self.config, 0, 5, location[0], location[1])]
                attack = path_finder.calc_dynamic_shortest_path(location, units, combo)
                gamelib.debug_write("({},{}) scouts: {}, demolishers: {}, damage: {}".format(location[0], location[1], combo[0],combo[1], sum(attack["remain_quantities"])))
                if sum(attack["remain_quantities"]) > best_attack["damage"]:
                    best_attack = {"num_scouts": combo[0], "num_demolisher": combo[1], "location": location, "damage": sum(attack["remain_quantities"])}
        

        attack_turn = best_attack["damage"] > min(game_state.enemy_health, 5)

        # best_attack = {"num_scouts":2, "num_demolisher": 2, "location": [6,7], "damage": 0}
        # if total_mp > 10:
        if attack_turn:
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

