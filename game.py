import logging

import definitions
# from world import CONNECT, AREAS, MAP, KEY
from enum import Enum, auto
from logger_format import get_logger
from world import World
from definitions import generate_random_name
import random

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
    def __init__(self, player_id, name, human, ai_type=None) -> object:
        self.player_id = player_id

        if name is None:
            self.name = generate_random_name()
        else:
            self.name = name

        self.human = human
        self.ai_type = ai_type
        self.continents_owned = []
        self.territories_owned = []
        self.army_reserve = 0

    @classmethod
    def add_human_player(cls, player_id, name):
        return cls(player_id, name, human=True)

    @classmethod
    def add_ai_player(cls, player_id, name):
        return cls(player_id, name, human=False)

    def get_player_feedback(self, print_msg, allowable_actions):
        if self.human:
            feedback = self.get_human_feedback(print_msg, allowable_actions)
        else:
            get_ai_feedback(self)

        return feedback

    def get_human_feedback(self, print_msg, allowable_actions):
        print(print_msg)
        while True:
            attempt = input()
            if attempt in allowable_actions:
                return attempt
            else:
                print('Invalid selection, input again')

    def get_ai_feedback(self):
        print('ai not programmed yet')
        raise KeyError

    # def claim_country(self, territory_id):
    #     """ Claim unoccupied country"""
    #     pass

    def __lt__(self, other):
        return self.player_id < other.player_id

    def __eq__(self, other):
        if isinstance(other, int):
            return self.player_id == other
        elif isinstance(other, Player):
            return self.player_id == other.player_id
        elif isinstance(other, str):
            if other.isnumeric():
                return self.player_id == int(other)
            else:
                return self.name == other
        else:
            return False

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

    def __lt__(self, other):
        return self.card_num < other.card_num

def create_territory_deck():
    return [Card(card_num) for card_num in definitions.territory_cards.keys()]


class Game:
    def __init__(self) -> object:
        self.options = {}
        self.options["num_human_players"] = 3
        self.options["autodeal_territories"] = True # Normal game set this to false


        self.num_human_players = self.options["num_human_players"]

        self.game_phase = GamePhases.INITIAL_ARMY_PLACEMENT
        self.game_over = False

        self.card_deck = create_territory_deck()
        self.discard_pile = []
        self.army_bonus = calculate_next_army_bonus()

        self.world = World()

        self.players = self.seat_players()
        self.num_players = len(self.players)  # turn order is order in list


    def play(self):
        self.play_initial_army_placement()

    def change_territory_owner(self, territory_id, owner_id, num_armies):
        self.world.change_territory_owner(territory_id, owner_id, num_armies)

    def player_claim_initial_territory(self, territory_id, owner_id):
        self.change_territory_owner(territory_id, owner_id, 1)
        self.adjust_player_army_reserve(owner_id, -1)
        self.world.update_world()

    def seat_players(self):
        players = [Player.add_human_player(i, None) for i in range(self.num_human_players)]
        random.shuffle(players)
        return players

    def adjust_player_army_reserve(self, player_id, reserve_adjustment):
        player = self.get_player(player_id)
        player.army_reserve += reserve_adjustment

    def get_player(self, player_id):
        player_index = self.players.index(player_id)
        player = self.players[player_index]
        return player

    def play_initial_army_placement(self):
        starting_armies = definitions.starting_armies[self.num_players]
        for player in self.players:
            # Assign correct initial armies
            player.army_reserve = starting_armies
        self.world.update_world()

        while not self.world.world_occupied:
            for player in self.players:
                player_message = "Player " + str(player.player_id) + " (" + player.name + "): Input country desired"
                player_choice = player.get_player_feedback(player_message, [str(i) for i in self.world.allowable_placement_countries()])
                print("Player " + str(player.player_id) + " (" + player.name + "): selected " + str(player_choice))
                self.player_claim_initial_territory(int(player_choice), player.player_id)




if __name__ == "__main__":
    game_log.info('Initialize Session')

    game = Game()

    while not game.game_over:
        game.play()

        game.game_over = True
