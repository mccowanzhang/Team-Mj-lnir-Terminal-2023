import unittest
import json
from .game_state import GameState

with open("../game-configs.json", 'r') as f:
    config = json.load(f)

class BasicTests(unittest.TestCase):

    def make_turn_0_map(self):
        turn_0 = """{"p2Units":[[],[],[],[],[],[],[]],"turnInfo":[0,0,-1],"p1Stats":[30.0,25.0,5.0,0],"p1Units":[[],[],[],[],[],[],[]],"p2Stats":[30.0,25.0,5.0,0],"events":{"selfDestruct":[],"breach":[],"damage":[],"shield":[],"move":[],"spawn":[],"death":[],"attack":[],"melee":[]}}"""
        
        state = GameState(config, turn_0)
        state.suppress_warnings(True)
        return state

    def test_basic(self):
        self.assertEqual(True, True, "It's the end of the world as we know it, and I feel fine")

    def test_simple_fields(self):
        game = self.make_turn_0_map()
        self.assertEqual(5, game.get_resource(game.MP), "I should have 5 MP")
        self.assertEqual(25, game.get_resource(game.SP), "I should have 25 SP")
        self.assertEqual(5, game.get_resource(game.MP, 1), "My opponent should have 5 MP")
        self.assertEqual(25, game.get_resource(game.SP, 1), "My opponent should have 25 SP")
        self.assertEqual(0, game.turn_number, "The map does not have a turn_number, or we can't read it")
        self.assertEqual(30, game.my_health, "My integrity is not working")
        self.assertEqual(30, game.enemy_health, "My opponent has no integrity!")

    def test_spawning(self):
        game = self.make_turn_0_map()
        self.assertEqual(True, game.attempt_spawn("SI", [[13, 0]]), "We cannot spawn a soldier!")
        self.assertEqual(False, game.attempt_spawn("SI", [[13, 13]]), "We can spawn a soldier in the middle of the map?!?!")
        self.assertEqual(False, game.can_spawn("FF", [14, 14]), "Apparently I can place towers on my opponent's side")
        self.assertEqual(True, game.attempt_spawn("DF", [[13, 6]]), "We cannot spawn a tower!")
        self.assertEqual(2, game.attempt_spawn("SI", [[13, 0], [13, 0], [13, 5]]), "More or less than 2 units were spawned!")
        self.assertEqual([("DF", 13, 6)], game._build_stack, "Build queue is wrong!")
        self.assertEqual([("SI", 13, 0), ("SI", 13, 0), ("SI", 13, 0)], game._deploy_stack, "Deploy queue is wrong!")

    def test_trivial_functions(self):
        game = self.make_turn_0_map()

        #Distance Between locations
        self.assertEqual(1, game.game_map.distance_between_locations([0, 0], [0,-1]), "The distance between 0,0 and 0,-1 should be 1")
        self.assertEqual(1, game.game_map.distance_between_locations([-1, -1], [-2,-1]), "The distance between -1,-1 and -2,-1 should be 1")
        self.assertEqual(5, game.game_map.distance_between_locations([0, 0], [4, 3]), "The distance between 0,0 and 16,9 should be 5")
        self.assertEqual(0, len(game.game_map.get_locations_in_range([-500,-500], 10)), "Invalid tiles are being marked as in range")
        self.assertEqual(1, len(game.game_map.get_locations_in_range([13,13], 0)), "A location should be in range of itself")
    
    def test_get_units(self):
        game = self.make_turn_0_map()
        self.assertEqual(0, len(game.game_map[13,13]), "There should not be a unit on this location")
        for _ in range(3):
            game.game_map.add_unit("EI", [13,13])
        self.assertEqual(3, len(game.game_map[13,13]), "Information seems not to be stacking")
        for _ in range(3):
            game.game_map.add_unit("FF", [13,13])
        self.assertEqual(1, len(game.game_map[13,13]), "Towers seem to be stacking")
        
    def test_get_units_in_range(self):
        game = self.make_turn_0_map()
        self.assertEqual(1, len(game.game_map.get_locations_in_range([13,13], 0)), "We should be in 0 range of ourself")
        self.assertEqual(37, len(game.game_map.get_locations_in_range([13,13], 3.5)), "Wrong number of tiles in range")

    def _test_get_attackers(self):
        game = self.make_turn_0_map()
        
        self.assertEqual([], game.get_attackers([13,13], 0), "Are we being attacked by a ghost?")
        game.game_map.add_unit("DF", [12,12], 0)
        self.assertEqual([], game.get_attackers([13,13], 0), "Are we being attacked by a friend?")
        game.game_map.add_unit("EF", [13,12], 1)
        self.assertEqual([], game.get_attackers([13,13], 0), "Are we being attacked by a support?")
        game.game_map.add_unit("FF", [14,12], 1)
        self.assertEqual([], game.get_attackers([13,13], 0), "Are we being attacked by a wall?")
        game.game_map.add_unit("DF", [12,14], 1)
        self.assertEqual(1, len(game.get_attackers([13,13], 0)), "We should be in danger")
        game.game_map.add_unit("DF", [13,14], 1)
        game.game_map.add_unit("DF", [14,14], 1)
        self.assertEqual(3, len(game.get_attackers([13,13], 0)), "We should be in danger from 3 places")

    def test_print_unit(self):
        game = self.make_turn_0_map()

        game.game_map.add_unit("FF", [14,13], 1)
        got_string = str(game.game_map[14,13][0])
        expected_string = "Enemy FF, health: 75.0 location: [14, 13] removal:  upgrade: False "
        self.assertEqual(got_string, expected_string, "Expected {} from print_unit test got {} ".format(expected_string, got_string))

    def test_future_MP(self):
        game = self.make_turn_0_map()

        self.future_turn_testing_function(game, 8.3, 1)
        self.future_turn_testing_function(game, 11.6, 2)
        self.future_turn_testing_function(game, 13.7, 3)

    def future_turn_testing_function(self, game, expected, turns):
        actual = game.project_future_MP(turns)
        self.assertAlmostEqual(actual, expected, 0, "Expected {} MP {} turns from now, got {}".format(expected, turns, actual))

