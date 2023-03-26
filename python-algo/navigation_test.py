# basic tests
from gamelib.tests import BasicTests
from gamelib.custom_navigation import CustomPathFinder
from gamelib.unit import GameUnit

bt = BasicTests()

def test_custom_navigation_1():
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

    unit = GameUnit("PI", config, 0, None, x = 13, y = 0)
    resp = cpf.calc_dynamic_shortest_path((13, 0), unit, 5)
    return resp

def test_custom_navigation_2():
    gs = bt.make_turn_0_map()
    # a single turret
    gs.game_map.add_unit("DF", (26, 15), 1)

    config = gs.config

    cpf = CustomPathFinder(config)
    cpf.initialize_map(gs)
    cpf.prep_static_shortest_path()

    unit = GameUnit("PI", config, 0, None, x = 13, y = 0)
    resp = cpf.calc_dynamic_shortest_path((13, 0), unit, 5)
    return resp

def test_custom_navigation_3():
    gs = bt.make_turn_0_map()
    # a single turret
    gs.game_map.add_unit("DF", (26, 15), 1)

    config = gs.config

    cpf = CustomPathFinder(config)
    cpf.initialize_map(gs)
    cpf.prep_static_shortest_path()

    units = []
    units.append(GameUnit("PI", config, 0, None, x = 13, y = 0))
    units.append(GameUnit("EI", config, 0, None, x = 13, y = 0))

    resp = cpf.calc_dynamic_shortest_path((13, 0), units, [1, 1])
    return resp

def test_self_destruct():
    gs = bt.make_turn_0_map()
    for i in range(28):
        gs.game_map.add_unit('FF', (i, 14), 1)

    config = gs.config

    cpf = CustomPathFinder(config)
    cpf.initialize_map(gs)
    cpf.prep_static_shortest_path()

    unit = GameUnit("PI", config, 0, None, x = 14, y = 0)
    resps = []
    for loc in cpf.game_map.get_edge_locations(2):
        resps.append(cpf.calc_dynamic_shortest_path(loc, unit, 1))
    return resps

def test_six_scouts_bug():
    gs = bt.make_turn_0_map()
    gs.game_map.add_unit('DF', (6, 16), 1)
    gs.game_map.add_unit('DF', (13, 17), 1)
    gs.game_map.add_unit('DF', (18, 16), 1)
    gs.game_map.add_unit('DF', (21, 18), 1)
    gs.game_map.add_unit('DF', (25, 14), 1)

    config = gs.config

    cpf = CustomPathFinder(config)
    cpf.initialize_map(gs)
    cpf.prep_static_shortest_path()

    unit = GameUnit("SI", config, 0, None, x = 6, y = 7)
    resp = cpf.calc_dynamic_shortest_path((6, 7), unit, 5)
    return resp

def strategy_test():
    gs = bt.make_turn_0_map()

    gs.game_map.add_unit("FF", (25, 14), 1)
    gs.game_map.add_unit("FF", (26, 14), 1)
    gs.game_map.add_unit("FF", (27, 14), 1)
    gs.game_map.add_unit("FF", (25, 15), 1)
    gs.game_map.add_unit("FF", (26, 15), 1)
    gs.game_map.add_unit("FF", (25, 16), 1)

    config = gs.config
    from strategies import CornerAttack
    strategy = CornerAttack(config)
    strategy.play_turn(gs)