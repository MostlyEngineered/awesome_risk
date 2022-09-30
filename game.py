import logging

import definitions

# from world import CONNECT, AREAS, MAP, KEY
from aenum import Enum, auto, unique, extend_enum
from logger_format import get_logger
from world import World
from definitions import generate_random_name
import random

game_log = get_logger("GameLog", file_name="game_log.txt", logging_level="info")
program_log = get_logger("ProgramLog", file_name="program_errors.txt", logging_level="error")
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


@unique
class GamePhases(Enum):
    INITIAL_ARMY_PLACEMENT = auto()
    INITIAL_ARMY_FORTIFICATION = auto()
    PLAYER_CARD_CHECK = auto()
    PLAYER_PLACE_NEW_ARMIES = auto()
    PLAYER_ATTACKING = auto()
    PLAYER_FORTIFICATION = auto()


@unique
class PlayerPhases(Enum):
    INITIAL_ARMY_PLACEMENT = GamePhases.INITIAL_ARMY_PLACEMENT
    INITIAL_ARMY_FORTIFICATION = GamePhases.INITIAL_ARMY_FORTIFICATION
    PLAYER_CARD_CHECK = GamePhases.PLAYER_CARD_CHECK
    PLAYER_PLACE_NEW_ARMIES = GamePhases.PLAYER_PLACE_NEW_ARMIES
    PLAYER_ATTACKING = GamePhases.PLAYER_ATTACKING
    PLAYER_FORTIFICATION = GamePhases.PLAYER_FORTIFICATION

    PLAYER_ATTACKING_FROM = auto()
    PLAYER_ATTACKING_TO = auto()
    PLAYER_FORTIFICATION_FROM = auto()
    PLAYER_FORTIFICATION_TO = auto()
    PLAYER_CARD_PICK = auto()


class Player:
    def __init__(self, player_id, name) -> object:
        self.human = True
        self.initialize_player(player_id, name, self.human)

        # TODO clean up initialization of Player, utilize the action_space in the code
        # TODO organize Player code into separate file
        # TODO organize folder for bots to allow easier selection

    def initialize_player(self, player_id, name, human):

        self.player_id = player_id

        if name is None:
            self.name = generate_random_name()
        else:
            self.name = name

        self.human = human

        self.continents_owned = []
        self.territories_owned = []
        self.army_reserve = 0
        self.action_space = None

    def get_player_feedback(self, print_msg, allowable_actions):
        if self.human:
            feedback = self.get_human_feedback(print_msg, allowable_actions)
        else:
            get_ai_feedback(self)

        return feedback

    def get_human_feedback(self, print_msg, allowable_actions):
        print(print_msg)
        allowable_actions = [str(i) for i in allowable_actions]
        while True:
            attempt = input()
            if attempt in allowable_actions:
                return attempt
            else:
                print("Invalid selection, input again")

    def get_ai_feedback(self):
        print("ai not programmed yet")
        raise KeyError

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


class Bot(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name, bot_type):
        self.bot_type = bot_type  # TODO clean up initialization of bot
        self.initialize_player(player_id, name, False)

    def get_action(self, game_state):
        if game_state == PlayerPhases.INITIAL_ARMY_PLACEMENT:
            pass
        elif game_state == GamePhases.INITIAL_ARMY_FORTIFICATION:
            pass
        elif game_state == GamePhases.PLAYER_CARD_CHECK:
            pass
        elif game_state == GamePhases.PLAYER_PLACE_NEW_ARMIES:
            pass
        elif game_state == GamePhases.PLAYER_ATTACKING:
            pass
        elif game_state == GamePhases.PLAYER_FORTIFICATION:
            pass
        elif game_state == GamePhases.PLAYER_ATTACKING_FROM:
            pass
        elif game_state == GamePhases.PLAYER_ATTACKING_TO:
            pass
        elif game_state == GamePhases.PLAYER_FORTIFICATION_FROM:
            self.select_fortification_from()
        elif game_state == GamePhases.PLAYER_FORTIFICATION_TO:
            self.select_fortification_to()
        elif game_state == GamePhases.PLAYER_CARD_PICK:
            pass
        else:
            pass

    def select_initial_army_placement(self):
        raise NotImplementedError()

    def select_initial_army_fortification(self):
        raise NotImplementedError()

    def select_card_decision(self):
        raise NotImplementedError()

    def select_cards_to_use(self):
        raise NotImplementedError()

    def place_new_armies(self):
        raise NotImplementedError()

    def select_attack_from(self):
        raise NotImplementedError()

    def select_attack_to(self):
        raise NotImplementedError()

    def select_fortification_from(self):
        raise NotImplementedError()

    def select_fortification_to(self):
        raise NotImplementedError()


class Card:
    def __init__(self, card_num) -> object:
        self.card_num = card_num
        if (card_num > max(CARD_DECK.keys())) or (card_num < min(CARD_DECK.keys())):
            program_log.error("Illegal card ref creation")
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
        self.options["num_human_players"] = 0
        self.options["computer_ai"] = ["random_ai", "random_ai", "random_ai"]
        self.options["autodeal_territories"] = True  # Normal game set this to false
        self.options[
            "initial_army_placement_batch_size"
        ] = 1  # How many armies a player places at a time after initial country selection

        self.num_human_players = self.options["num_human_players"]

        self.game_phase = GamePhases.INITIAL_ARMY_PLACEMENT
        self.game_over = False

        self.card_deck = create_territory_deck()
        self.discard_pile = []
        self.army_bonus = calculate_next_army_bonus()

        self.world = World()

        self.players = self.seat_players()
        self.num_players = len(self.players)  # turn order is order in list
        self.game_army_reserves = 0
        self.out_players = []
        self.current_game_action_space = []

    def calculate_game_army_reserves(self):
        """ Calculate if all army reserves have been placed"""
        self.game_army_reserves = sum([player.army_reserve for player in self.players])

    def play(self):
        self.play_initial_army_placement()
        self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION
        self.play_initial_army_fortification()

        while not self.game_over:
            for player in self.players:
                if player in self.players:  # Players can be eliminated out of list
                    self.play_player_turn(player)

    def change_territory_owner(self, territory_id, owner_id, num_armies):
        """ Change territory owner and change number of armies in territory"""
        self.world.change_territory_owner(territory_id, owner_id, num_armies)

    def player_claim_initial_territory(self, territory_id, owner_id):
        """ Claim initial territory, place one army from their reserve in the territory """
        self.change_territory_owner(territory_id, owner_id, 1)
        self.adjust_player_army_reserve(owner_id, -1)
        self.world.update_world()

    def seat_players(self):
        """ Seat all players (currently only human players)"""
        players = [Player(i, None) for i in range(self.num_human_players)]
        for comp_player in self.options["computer_ai"]:
            players = players + [Bot(player_id=len(players), name=None, bot_type=comp_player)]
        random.shuffle(players)
        return players

    def adjust_player_army_reserve(self, player_id, reserve_adjustment):
        """ Adjust player army reserve by reserve_adjustment"""
        player = self.get_player(player_id)
        player.army_reserve += reserve_adjustment

    def adjust_territory_army_number(self, territory_id, army_number, addition_mode=True):
        """ adjust number of armies in a territory by setting or addition"""
        if addition_mode:
            # Addition mode
            self.world.territories[territory_id].num_armies += army_number
        else:
            # Set mode
            self.world.territories[territory_id].num_armies = army_number

    def get_player(self, player_id):
        player_index = self.players.index(player_id)
        player = self.players[player_index]
        return player

    def get_allowable_initial_fortifications(self, player_id):
        return [territory.territory_id for territory in self.world.territories if territory.owner_id == player_id]

    def player_select_initial_placements(self):
        while not self.world.world_occupied:
            for player in self.players:
                player_message = "Player " + str(player.player_id) + " (" + player.name + "): Input country desired"
                self.current_game_action_space = [str(i) for i in self.world.allowable_placement_countries()]
                player_choice = player.get_player_feedback(player_message, self.current_game_action_space)
                self.player_claim_initial_territory(int(player_choice), player.player_id)
                game_log.info(
                    "Player " + str(player.player_id) + " (" + player.name + "): selected " + str(player_choice)
                )

    def autodeal_initial_placements(self):
        while not self.world.world_occupied:
            for player in self.players:
                selected_territory_id = random.choice(self.world.allowable_placement_countries())
                self.player_claim_initial_territory(int(selected_territory_id), player.player_id)
                game_log.info(
                    "Player "
                    + str(player.player_id)
                    + " ("
                    + player.name
                    + "): autodealt "
                    + str(selected_territory_id)
                )

    def play_initial_army_placement(self):
        starting_armies = definitions.starting_armies[self.num_players]
        for player in self.players:
            # Assign correct initial armies
            player.army_reserve = starting_armies
        self.world.update_world()
        if self.options["autodeal_territories"]:
            self.autodeal_initial_placements()
        else:
            self.player_select_initial_placements()

    def play_initial_army_fortification(self):
        game_log.info("Start initial fortification")
        batch_size = self.options["initial_army_placement_batch_size"]
        while game.game_phase == GamePhases.INITIAL_ARMY_FORTIFICATION:
            for player in self.players:
                self.current_game_action_space = self.get_allowable_initial_fortifications(player.player_id)
                for placement in range(batch_size):
                    if player.army_reserve <= 0:
                        continue
                    player_message = "Player " + str(player.player_id) + " (" + player.name + "): Input country desired"
                    selected_territory_id = player.get_player_feedback(player_message, self.current_game_action_space)
                    self.adjust_player_army_reserve(player.player_id, -1)
                    self.adjust_territory_army_number(int(selected_territory_id), 1, addition_mode=True)
                    game_log.info(
                        "Player "
                        + str(player.player_id)
                        + " ("
                        + player.name
                        + "): added army to "
                        + str(selected_territory_id)
                    )
                self.calculate_game_army_reserves()
                if self.game_army_reserves <= 0:
                    self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION

    def play_player_turn(self, player):
        self.game_phase = GamePhases.PLAYER_FORTIFICATION

        self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES

        self.game_phase = GamePhases.PLAYER_ATTACKING

        self.game_phase = GamePhases.PLAYER_FORTIFICATION


if __name__ == "__main__":
    game_log.info("Initialize Session")

    game = Game()

    while not game.game_over:
        game.play()

        game.game_over = True
