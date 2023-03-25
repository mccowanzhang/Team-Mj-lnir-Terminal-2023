# basic tests
from gamelib.tests import BasicTests
from gamelib.custom_navigation import CustomPathFinder
from gamelib.unit import GameUnit

bt = BasicTests()
gs = bt.make_turn_0_map()
gs.game_map.add_unit("FF", (25, 14), 1)
gs.game_map.add_unit("FF", (26, 14), 1)
gs.game_map.add_unit("FF", (27, 14), 1)
gs.game_map.add_unit("FF", (25, 15), 1)
gs.game_map.add_unit("FF", (26, 15), 1)
gs.game_map.add_unit("FF", (25, 16), 1)

config = gs.config

cpf = CustomPathFinder(config)
cpf.initialize_map(gs)
cpf.prep_static_shortest_path()
# manually create a block here xd
cpf.node_map[27][14].blocked = True
print(cpf.calc_static_shortest_path((13, 0))[0])

unit = GameUnit("PI", config, 0, None, x = 13, y = 0)
resp = cpf.calc_dynamic_shortest_path((13, 0), unit, quantity=5)
print(resp["dynamic_path"])
