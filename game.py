import logging

import definitions
# from world import CONNECT, AREAS, MAP, KEY
from enum import Enum, auto
from logger_format import get_logger
from world import World

game_log = get_logger('GameLog', file_name='game_log.txt', logging_level='info')
program_log = get_logger('ProgramLog', file_name='program_errors.txt', logging_level='error')
CARD_DECK = definitions.territory_cards


def calculate_next_army_bonus(previous_bonus=0):
    initial_army_bonus = 4
    if previous_bonus == 0:
        return initial_army_bonus

    bonus_order = (4, 6, 8, 10, 12, 15)
    max_list_bonus = max(bonus_order)
    try:
        if previous_bonus < max_list_bonus:
            current_index = bonus_order.index(previous_bonus)
            return bonus_order[current_index + 1]
        else:
            # if bonus is equal to biggest bonus or more add 5
            return previous_bonus + 5
    except KeyError:
        program_log.error("invalid bonus suggested")
        raise KeyError


class GamePhases(Enum):
    INITIAL_ARMY_PLACEMENT = auto()


class Player:
    def __init__(self) -> object:
        self.id = -1  # TODO add player function
        self.name = ""  # TODO add player function
        self.player_type = "human"  # TODO this needs to handle ai
        self.continents_owned = []
        self.territories_owned = []

    def add_human_player(self):
        pass

class Card:
    def __init__(self, card_num) -> object:
        self.card_num = card_num
        if (card_num > max(CARD_DECK.keys())) or (card_num < min(CARD_DECK.keys())):
            program_log.error('Illegal card ref creation')
            raise KeyError
        else:
            self.card_type = definitions.territory_cards[card_num]

        if self.card_type == definitions.CardType.WILD:
            self.territory_id = None
            self.territory = None
        else:
            self.territory_id = card_num
            self.territory = definitions.territory_names[self.territory_id]


def create_territory_deck():
    return [Card(card_num) for card_num in definitions.territory_cards.keys()]

class Game:
    def __init__(self) -> object:
        self.options = {}

        self.game_phase = GamePhases.INITIAL_ARMY_PLACEMENT
        self.game_over = False

        self.card_deck = create_territory_deck()
        self.discard_pile = []
        self.army_bonus = calculate_next_army_bonus()

        self.world = World()

        self.players = seat_players()
        self.num_players = len(self.players)
        self.turn_order = (0, )  # create turn order off players

    def play(self):
        pass

    def seat_players(self):
        pass

    def play_initial_army_placement(self):
        while not self.world.world_occupied:


if __name__ == "__main__":
    game_log.info('Initialize Session')

    game = Game()

    while not game.game_over:
        game.play()



        game.game_over = True
