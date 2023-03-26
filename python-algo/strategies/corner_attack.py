from .strategy import Strategy

class CornerAttack(Strategy):
    def __init__(self, config, EDGES, tiles):
        super().__init__(config, EDGES, tiles)
        # defense parameters
        self.DEFEND_LEFT_THRESHOLD = 9
        self.DEFEND_RIGHT_THRESHOLD = 18

        # structure placements
        self.l_turret_locations = [[6,12],[2,12]]
        self.r_turret_locations = [[21,12],[25,12]]
        self.c_turret_locations = [[11,6],[16,6]]
        self.l_upgraded_wall_locations = [[0,13],[5,13]]
        self.r_upgraded_wall_locations = [[22,13], [27,13]]
        self.l_chamber_wall_locations = [[1,13],[2,12],[3,12],[4,11],[5,10],[6,9],[6,8]]
        self.r_chamber_wall_locations = [[26,13],[25,12],[24,12],[23,11],[22,10],[21,9],[21,8]]

        self.l_defense_wall_locations =[[5,13],[0,13],[1,13],[2,13],[3,12]]
        self.r_defense_wall_locations =[[22,13],[27,13],[26,13],[25,13],[24,12]]

        self.l_navigation_wall_locations =[[5,13],[6,12],[7,11],[8,10],[9,9],[10,8],[11,7],[12,6],[13,5]]
        self.r_navigation_wall_locations =[[22,13],[21,12],[20,11],[19,10],[18,9],[17,8],[16,7],[15,6],[14,5]]
        self.upgraded_support_locations = [[13,10],[14,10],[13,9],[14,9]]
        self.l_extra_turret_locations = [[2,11],[2,13],[7,12],[8,11],[7,8],[8,7]]
        self.c_extra_turret_locations = [[12,5],[15,5],[13,4],[14,4],[16,19],[16,8],[10,8]]
        self.r_extra_turret_locations = [[25,11],[24,13],[20,12],[19,11],[20,8],[19,7]]
        self.extra_extra_support_locations = [[11,10],[12,10],[11,9],[12,9],[15,10],[16,10],[15,9],[16,9],[13,8],[14,8],[13,7],[14,7]]

        # mobile placements
        self.l_one_chamber_locations = [[1,12]]
        self.r_one_chamber_locations = [ [26,12]]
        self.l_three_chamber_locations = [[4,9]]
        self.r_three_chamber_locations = [[23,9]]
        self.attack_locations = [[6,7],[7,6],[8,5],[9,4],[10,3],[11,2],[12,1],[13,0],[14,0],[15,1],[16,2],[17,3],[18,4],[19,5],[20,6],[21,7]]

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
        game_state.attempt_spawn(TURRET, self.l_turret_locations)
        game_state.attempt_spawn(TURRET, self.r_turret_locations)
        game_state.attempt_spawn(WALL, self.l_upgraded_wall_locations)
        game_state.attempt_upgrade(self.l_upgraded_wall_locations)
        game_state.attempt_spawn(WALL, self.r_upgraded_wall_locations)
        game_state.attempt_upgrade(self.r_upgraded_wall_locations)

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

