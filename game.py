import numpy as np
import definitions
from logger_format import get_logger
from player import *  # Import all bots from player
from world import World
from definitions import PlayerPhases, GamePhases, CardPhases, CardType, territory_locations, territory_names
import random
from combat import resolve_combat
import time

import os

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

game_log = get_logger("GameLog", file_name="game_log.txt", logging_level="info", clear_previous_logs=True)
program_log = get_logger("ProgramLog", file_name="program_errors.txt", logging_level="error")
CARD_DECK = definitions.territory_cards

def flatten_list(over_list):
    flat_list = [item for sublist in over_list for item in sublist]
    removed_duplicates = list(set(flat_list))
    return removed_duplicates


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


class Card:
    def __init__(self, card_num) -> object:
        self.card_num = card_num
        if (card_num > max(CARD_DECK.keys())) or (card_num < min(CARD_DECK.keys())):
            program_log.error("Illegal card ref creation")
            raise KeyError
        else:
            self.card_type = definitions.territory_cards[card_num]

        if self.card_type == CardType.WILD:
            self.territory_id = None
            self.territory = None
        else:
            self.territory_id = card_num
            self.territory = territory_names[self.territory_id]

        self.card_value = {CardType.CAVALRY: 0, CardType.INFANTRY: 0, CardType.ARTILLERY: 0}
        if self.card_type == CardType.WILD or self.card_type == CardType.CAVALRY:
            self.card_value[CardType.CAVALRY] = 1
        if self.card_type == CardType.WILD or self.card_type == CardType.INFANTRY:
            self.card_value[CardType.INFANTRY] = 1
        if self.card_type == CardType.WILD or self.card_type == CardType.ARTILLERY:
            self.card_value[CardType.ARTILLERY] = 1

    def __lt__(self, other):
        return self.card_num < other.card_num

def create_territory_deck():
    card_deck = [Card(card_num) for card_num in definitions.territory_cards.keys()]
    random.shuffle(card_deck)
    return card_deck


class Game:
    # TODO make sure action_space for players is updated consistently
    # TODO make sure game_state and player_state are updated consistently
    def __init__(self, game_options) -> object:
        self.game_options = game_options

        self.num_human_players = self.game_options["num_human_players"]

        default_game_options = {
            "turn_limit": np.inf,
            "disable_cards": False,
            "always_maximal_attack": True,
            "autodeal_territories": False,
            "berzerker_mode": False,

            "headless": False,
            "fortification_limit": 100,
            "bot_sleep": None,
        }

        for option in default_game_options.keys():
            if option not in self.game_options.keys():
                self.game_options[option] = default_game_options[option]

        self.game_phase = GamePhases.INITIAL_ARMY_PLACEMENT
        self.game_over = False

        self.card_deck = create_territory_deck()
        self.discard_pile = []
        self.playing_cards = []  # Temp list for playing cards

        self.army_bonus = calculate_next_army_bonus()

        self.world = World()

        self.players = self.seat_players()
        self.num_players = len(self.players)  # turn order is order in list
        self.game_army_reserves = 0
        self.out_players = []
        self.turn = 0
        self.im = None
        self.territory_names_str = self.get_territory_names()

        self.current_player = None
        self.next_player(initial=True)

        self.initialize_board()
        self.game_phase = GamePhases.INITIAL_ARMY_PLACEMENT  # First state in game

        for player in self.players:
            # Assign correct initial armies
            player.army_reserve = definitions.starting_armies[self.num_players]
        self.world.update_world()
        self.calculate_game_army_reserves()

        if self.game_options["autodeal_territories"]:
            self.autodeal_initial_placements()
            self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION

        self.calculate_player_action_space(self.current_player)

    def seat_players(self):
        """Seat all players (currently only human players)"""

        players = [Human(i, None) for i in range(self.num_human_players)]

        for comp_player in self.game_options["computer_ai"]:
            players = players + [eval(comp_player)(player_id=len(players), name=None, bot_type=comp_player)]
        random.shuffle(players)
        return players

    def step_action(self, action):
        """ After this the action space will be calculated so this needs to end on the correct next player"""
        if self.game_phase == GamePhases.INITIAL_ARMY_PLACEMENT and not self.game_options["autodeal_territories"]:
            self.step_select_initial_placements(action)
            self.world.update_world()
            self.next_player()
            if not len(self.world.available_territories):
            # Once all available territories are taken proceed to next game phase
                self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION
                self.current_player = self.players[0]  # First player fortifies first in next phase
            return

        if self.game_phase == GamePhases.INITIAL_ARMY_FORTIFICATION:

            self.adjust_player_army_reserve(self.current_player.player_id, -1)
            self.adjust_territory_army_number(int(action), 1, addition_mode=True)
            self.calculate_game_army_reserves()

            if self.game_army_reserves <= 0:
                self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES

            return

        if self.game_phase == GamePhases.PLAYER_CARD_CHECK:
            return

        if self.game_phase == GamePhases.PLAYER_PLACE_NEW_ARMIES:

            return

        if self.game_phase == GamePhases.PLAYER_ATTACKING:

            return

        if self.game_phase == GamePhases.PLAYER_FORTIFICATION:
            
            return


    def game_step(self, action):
        """ This is the basic game loop
        For this to work with OpenAI gym the game must advance in steps to subsequent actions.
        So only one action should be taken each time this function is called.
        """

        self.step_action(action)
        self.calculate_player_action_space(self.current_player)

    def step_select_initial_placements(self, action):
        # player_choice = self.current_player.select_initial_army_placement(self.current_player.action_space)

        self.player_claim_initial_territory(int(action), self.current_player.player_id)
        game_log.info(self.current_player.get_player_tag() + ": selected " + str(action))

    def calculate_player_action_space(self, player):
        if self.game_phase == GamePhases.INITIAL_ARMY_PLACEMENT:
            player.action_space = [str(i) for i in self.world.allowable_placement_countries()]
        if self.game_phase == GamePhases.INITIAL_ARMY_FORTIFICATION:
            self.get_allowable_initial_fortifications(player.player_id)
        if self.game_phase == GamePhases.PLAYER_CARD_CHECK:
            return
        if self.game_phase == GamePhases.PLAYER_PLACE_NEW_ARMIES:
            return
        if self.game_phase == GamePhases.PLAYER_ATTACKING:
            return
        if self.game_phase == GamePhases.PLAYER_FORTIFICATION:
            return


    def next_player(self, initial=False):
        """Method to iterate to next player in line
        Only active players are in Game.players so moving to next will always work"""
        if initial:
            self.current_player = self.players[0]  # Iterate to next player at end of step
        else:
            next_player_id = self.players.index(self.current_player) + 1
            if next_player_id >= len(self.players):
                self.current_player = self.players[0]  # If past max index then reset to first element
            else:
                self.current_player = self.players[next_player_id]


    def get_territory_names(self):
        return_str = str(territory_names).replace(", ", "\n")
        return_str = return_str.replace("{", "").replace("}", "").replace("'", "")
        return return_str

    def initialize_board(self):
        if not self.game_options["headless"]:

            self.im = plt.imread(os.getcwd() + "/img/risk.png")
            plt.figure(figsize=(16, 24))
            _ = plt.imshow(self.im)


    def player_claim_initial_territory(self, territory_id, owner_id):
        """Claim initial territory, place one army from their reserve in the territory"""
        self.change_territory_owner(territory_id, owner_id, 1)
        self.adjust_player_army_reserve(owner_id, -1)
        self.world.update_world()

    def calculate_game_army_reserves(self):
        """Calculate if all army reserves have been placed"""
        self.game_army_reserves = sum([player.army_reserve for player in self.players])

    def get_allowable_initial_fortifications(self, player_id):
        return [territory.territory_id for territory in self.world.territories if territory.owner_id == player_id]

    def change_territory_owner(self, territory_id, owner_id, num_armies):
        """Change territory owner and change number of armies in territory"""
        self.world.change_territory_owner(territory_id, owner_id, num_armies)

    def adjust_player_army_reserve(self, player_id, reserve_adjustment):
        """Adjust player army reserve by reserve_adjustment"""
        player = self.get_player(player_id)
        player.army_reserve += reserve_adjustment

    def get_player(self, player_id):
        for _ in range(3):
            try:
                player_index = self.players.index(player_id)
                player = self.players[player_index]
                return player

            except ValueError:
                program_log.error("This ValueError occurs but in debugger evaluates")  # TODO figure this error out
        raise ValueError

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


if __name__ == "__main__":
    game_log.info("Initialize Session")

    options = {
        "num_human_players": 0,
        "computer_ai": ["BerzerkBot", "PacifistBot", "PacifistBot"],
        "autodeal_territories": False,

        "always_maximal_attack": True,
        "berzerker_mode": True,
        "turn_limit": 150,
        "headless": False,
    }  # At current skill level if game hasn't ended by 150 turns it's probably not ending

    # self.options["num_human_players"] = 3  # Case for a human game
    # self.options["computer_ai"] = []  # Case for a human game

    # self.options["computer_ai"] = ["random_ai"]  # Case for a single bot game
    game = Game(options)

    while not game.game_over:
        # TODO Get this to work, the reward and observation state will be taken care of in the gym code
        action = game.current_player.decide_step_action(game.current_player.action_space, msg="")
        game.game_step(action)

