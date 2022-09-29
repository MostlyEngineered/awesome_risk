import definitions
from logger_format import get_logger

program_log = get_logger('ProgramLog', file_name='program_errors.txt', logging_level='error')


class Territory:
    def __init__(self, territory_id, name, connections, owner_id=None):
        self.can_attack = False
        self.territory_id = territory_id
        self.name = name
        self.connections = connections
        self.owner_id = owner_id
        self.num_armies = 0

    def __lt__(self, other):
        return self.territory_id < other.territory_id


class World:
    def __init__(self) -> object:
        self.territories = create_territories()
        self.territories_occupied = 0
        self.num_territories = len(self.territories)
        self.world_occupied = False

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

    def change_territory_owner(self, territory_num, owner_id):
        pass

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
