import math
from .unit import GameUnit


class Tile:
    def __init__(self, x, y, is_edge):
        self.x = x
        self.y = y
        self.unit = None
        self.enemy_coverage = 0
        self.friendly_coverage = 0
        self.is_edge = is_edge
        self.friendly_shield = {}
        self.enemy_shield = {}
        self.updated = False

    def add_unit(self, unit_type):
        self.unit = unit_type

    def remove_unit(self):
        self.unit = None

    def add_shield(self, key, amount):
        if key < 392:
            self.friendly_shield.update({key: amount})
        else:
            self.enemy_shield.update({key: amount})

    def remove_shield(self, key):
        self.friendly_shield.pop(key, None)
        self.enemy_shield.pop(key, None)

    def update_enemy_coverage(self, change_amount):
        self.enemy_coverage += change_amount if not - change_amount > self.enemy_coverage else 0

    def update_friendly_coverage(self, change_amount):
        self.friendly_coverage += change_amount if not - change_amount > self.friendly_coverage else 0

    def get_friendly_coverage(self):
        return self.friendly_coverage

    def get_enemy_coverage(self):
        return self.enemy_coverage

    def get_friendly_shields(self):
        return self.friendly_shield

    def get_enemy_shields(self):
        return self.enemy_shield

    def get_health(self):
        return self.unit.health if self.unit else 0

    def get_location(self):
        return [self.x, self.y]

    def get_location_abs(self):
        return 28 * self.y + self.x


    def surrounding_locations(self, radius):
        locations = []

        for h_distance in range(1, math.floor(radius)):
            locations.append([self.x - h_distance, self.y])
            locations.append([self.x + h_distance, self.y])
        for v_distance in range(1, math.floor(radius)):
            max_h = math.floor(math.sqrt(radius**2 - v_distance**2))
            for hv_distance in range (max_h):
                locations.append([self.x - hv_distance, self.y - v_distance])
                locations.append([self.x + hv_distance, self.y - v_distance])
                locations.append([self.x - hv_distance, self.y + v_distance])
                locations.append([self.x + hv_distance, self.y + v_distance])

        return locations

    def surrounding_locations_abs(self, radius):
        return [location[0] * location[1] for location in self.surrounding_locations(radius)]


## Defense specific class
class FriendlyTile(Tile):
    def __init__(self, x, y, is_edge):
        super().__init__(x, y, is_edge)
        self.pathing = False


## Offense and Defense Prediction
class EnemyTile(Tile):
    def __init__(self, x, y, is_edge):
        super().__init__(x, y, is_edge)
        self.unit_history = []

    def round_history(self, unit_type):
        self.unit_history.append(unit_type)


