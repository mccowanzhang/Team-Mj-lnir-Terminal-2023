# basic tests
from gamelib.tests import BasicTests
from gamelib.custom_navigation import CustomPathFinder

bt = BasicTests()
gs = bt.make_turn_0_map()

cpf = CustomPathFinder()
cpf.initialize_map(gs)
cpf.prep_static_shortest_path()
# manually create a block here xd
cpf.node_map[27][14].blocked = True
print(cpf.calc_static_shortest_path((13, 0)))