import definitions
from logger_format import get_logger

program_log = get_logger("ProgramLog", file_name="program_errors.txt", logging_level="error")


class Territory:
    def __init__(self, territory_id, name, connections, owner_id=None):
        self.can_attack = False
        self.territory_id = territory_id
        self.name = name
        self.connections = connections
        self.owner_id = owner_id
        self.num_armies = 0

    def change_owner(self, owner_id, num_armies):
        self.owner_id = owner_id
        self.num_armies = num_armies

    def max_attack_with(self):
        max_attack = self.num_armies - 1
        if max_attack > 3:
            return 3
        elif max_attack <= 0:
            program_log.error("illegal max attack calculation")
        else:
            return max_attack

    def __lt__(self, other):
        if isinstance(other, int):
            return self.territory_id < other
        elif isinstance(other, str):
            if other.isnumeric():
                return self.territory_id < int(other)
            else:
                return False  # Name lookup is probably not super important
        elif isinstance(other, Territory):
            return self.territory_id < other.territory_id
        else:
            return False

    def __eq__(self, other):
        if isinstance(other, int):
            return self.territory_id == other
        elif isinstance(other, str):
            if other.isnumeric():
                return self.territory_id == int(other)
            else:
                return self.name == other
        elif isinstance(other, Territory):
            return self.territory_id == other.territory_id
        else:
            return False


class World:
    def __init__(self) -> object:
        self.territories = create_territories()
        self.territories_occupied = 0
        self.num_territories = len(self.territories)
        self.world_occupied = False
        self.available_territories = []

    def check_army_placement_complete(self):
        if self.territories_occupied == self.num_territories:
            self.world_occupied = True
            return True
        elif self.territories_occupied > self.num_territories:
            program_log.error("Illegal occupied count")
            raise ValueError
        else:
            self.world_occupied = False
            return False

    def update_available_territories(self):
        self.available_territories = [territory for territory in self.territories if territory.owner_id is None]

    def update_territory_count(self):
        self.update_available_territories()
        self.territories_occupied = self.num_territories - len(self.available_territories)
        if self.territories_occupied == self.num_territories:
            self.world_occupied = True

    def update_world(self):
        self.update_territory_count()

    def allowable_placement_countries(self):
        return [territory.territory_id for territory in self.available_territories]

    def change_territory_owner(self, territory_id, owner_id, num_armies):
        """ Don't use this method except from the game change_territory_owner method"""
        territory = self.territories[territory_id]
        territory.owner_id = owner_id
        territory.num_armies = num_armies


def create_territories():
    territories = []
    for territory_id in definitions.territory_names.keys():
        territory = Territory(
            territory_id, definitions.territory_names[territory_id], definitions.territory_neighbors[territory_id]
        )
        territories.append(territory)
    return territories


if __name__ == "__main__":
    world = World()
