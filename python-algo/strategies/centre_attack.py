from .strategy import Strategy

class CentreAttack(Strategy):
    def __init__(self, config, EDGES, tiles):
        super().__init__(config, EDGES, tiles)
        # defense parameters
        self.DEFEND_LEFT_THRESHOLD = 5
        self.DEFEND_RIGHT_THRESHOLD = 23

        # structure placements
        self.l_turret_locations = [[5,12],[2,12]]
        self.r_turret_locations = [[22,12],[25,12]]
        self.c_turret_locations = [[10,12],[17,12],[11,12],[16,12]]
        self.l_upgraded_wall_locations = [[0,13]]
        self.r_upgraded_wall_locations = [[27,13]]
        self.l_chamber_wall_locations = [[3,11],[4,11],[4,10],[5,12],[6,11],[6,10],[6,9],[6,8]]
        self.r_chamber_wall_locations = [[24,11],[23,11],[23,10],[22,12],[21,11],[21,10],[21,9],[21,8]]

        self.l_defense_wall_locations =[[11,13],[10,13],[5,13],[4,13],[6,13],[0,13],[9,13],[8,13],[7,13],[3,13],[2,13],[1,13]]
        self.r_defense_wall_locations =[[16,13],[17,13],[22,13],[23,13],[21,13],[27,13],[18,13],[19,13],[20,13],[24,13],[25,13],[26,13]]

        self.l_navigation_wall_locations =[[0,13],[1,13],[2,13],[3,13],[4,13],[5,13],[6,13],[7,13],[8,13],[9,13],[10,13],[11,13]]
        self.r_navigation_wall_locations =[[27,13],[26,13],[25,13],[24,13],[23,13],[22,13],[21,13],[20,13],[19,13],[18,13],[17,13],[16,13]]
        self.upgraded_support_locations = [[18,12],[9,12],[8,12],[19,12],[18,11],[9,11],[8,11],[19,11]]
        self.l_extra_turret_locations = [[3,12],[10,11],[4,12],[6,12],[11,11],[1,12]]
        self.c_extra_turret_locations = [[10,13],[17,13],[11,13],[16,13],[10,12],[17,12]]
        self.r_extra_turret_locations = [[24,12],[17,11],[23,12],[21,12],[16,11],[26,12]]
        self.extra_extra_support_locations = [[8,10],[18,10],[9,10],[19,10],[8,9],[18,9],[9,9],[19,9],[8,8],[18,8],[9,8],[19,8],[8,7],[18,7],[9,7],[19,7],[18,6],[9,6]]

        # mobile placements
        self.l_one_chamber_locations = [[3,10]]
        self.r_one_chamber_locations = [[24,10]]
        self.l_three_chamber_locations = [[5,8]]
        self.r_three_chamber_locations = [[22,8]]
        self.l_five_chamber_locations = [[6,7]]
        self.r_five_chamber_locations = [[21,7]]
        self.attack_locations = [[7,6],[8,5],[9,4],[10,3],[11,2],[12,1],[13,0],[14,0],[15,1],[16,2],[17,3],[18,4],[19,5],[20,6]]

        # global variables
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

    def opener(self, game_state):
        """
        starting map for this strat
        """
        game_state.attempt_spawn(TURRET, self.l_turret_locations[0])
        game_state.attempt_spawn(TURRET, self.r_turret_locations[0])
        game_state.attempt_spawn(TURRET, self.c_turret_locations[0:2])
        game_state.attempt_spawn(WALL, self.l_upgraded_wall_locations[0])
        game_state.attempt_upgrade(self.l_upgraded_wall_locations[0])
        game_state.attempt_spawn(WALL, self.r_upgraded_wall_locations[0])
        game_state.attempt_upgrade(self.r_upgraded_wall_locations[0])

        game_state.attempt_spawn(WALL, self.l_chamber_wall_locations)
        game_state.attempt_spawn(WALL, self.r_chamber_wall_locations)
        game_state.attempt_spawn(WALL, self.l_navigation_wall_locations)
        game_state.attempt_spawn(WALL, self.r_navigation_wall_locations)

    def bomb_counter(self, game_state, dir):
        if dir == self.LEFT:
            game_state.attempt_spawn(INTERCEPTOR, self.l_one_chamber_locations)
        else:
            game_state.attempt_spawn(INTERCEPTOR, self.r_one_chamber_locations)

    def deploy_three_chamber(self, game_state, dir, num):
        if dir == self.LEFT:
            game_state.attempt_spawn(INTERCEPTOR, self.l_three_chamber_locations, num)
        else:
            game_state.attempt_spawn(INTERCEPTOR, self.r_three_chamber_locations, num)

    def deploy_five_chamber(self,game_state, dir, num):
        if dir == self.LEFT:
            game_state.attempt_remove([6,8])
            game_state.attempt_spawn(WALL, [[7,8],[7,7]])
            game_state.attempt_spawn(INTERCEPTOR, self.l_five_chamber_locations, num)
        else:
            game_state.attempt_remove([21,8])
            game_state.attempt_spawn(WALL, [[20,8],[20,7]])
            game_state.attempt_spawn(INTERCEPTOR, self.r_five_chamber_locations, num)
