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
<<<<<<< HEAD
    INITIAL_ARMY_PLACEMENT = GamePhases.INITIAL_ARMY_PLACEMENT.value
    INITIAL_ARMY_FORTIFICATION = GamePhases.INITIAL_ARMY_FORTIFICATION.value
    PLAYER_CARD_CHECK = GamePhases.PLAYER_CARD_CHECK.value
    PLAYER_PLACE_NEW_ARMIES = GamePhases.PLAYER_PLACE_NEW_ARMIES.value
    PLAYER_ATTACKING = GamePhases.PLAYER_ATTACKING.value
    PLAYER_FORTIFICATION = GamePhases.PLAYER_FORTIFICATION.value
=======
    INITIAL_ARMY_PLACEMENT = GamePhases.INITIAL_ARMY_PLACEMENT
    INITIAL_ARMY_FORTIFICATION = GamePhases.INITIAL_ARMY_FORTIFICATION
    PLAYER_CARD_CHECK = GamePhases.PLAYER_CARD_CHECK
    PLAYER_PLACE_NEW_ARMIES = GamePhases.PLAYER_PLACE_NEW_ARMIES
    PLAYER_ATTACKING = GamePhases.PLAYER_ATTACKING
    PLAYER_FORTIFICATION = GamePhases.PLAYER_FORTIFICATION
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0

    PLAYER_ATTACKING_FROM = auto()
    PLAYER_ATTACKING_TO = auto()
    PLAYER_FORTIFICATION_FROM = auto()
    PLAYER_FORTIFICATION_TO = auto()
    PLAYER_CARD_PICK = auto()


class Player:
<<<<<<< HEAD
    """ Player class does not get instantiated as it will be missing a feedback option.  Instantiate a bot or a human."""

    def __init__(self, player_id, name) -> object:
        self.human = True
        # self.initialize_player(player_id, name)
=======
    def __init__(self, player_id, name) -> object:
        self.human = True
        self.initialize_player(player_id, name, self.human)
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0

        # TODO clean up initialization of Player, utilize the action_space in the code
        # TODO organize Player code into separate file
        # TODO organize folder for bots to allow easier selection

<<<<<<< HEAD
=======
    def initialize_player(self, player_id, name, human):

        self.player_id = player_id

>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0
        if name is None:
            self.name = generate_random_name()
        else:
            self.name = name
<<<<<<< HEAD
        self.player_id = player_id
        self.cards = []
=======

        self.human = human

>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0
        self.continents_owned = []
        self.territories_owned = []
        self.army_reserve = 0
        self.action_space = None
<<<<<<< HEAD
        self.player_state = None  # Update from PlayerState Enum

    # def get_player_feedback(self, print_msg, allowable_actions):
    #     if self.human:
    #         feedback = self.get_human_feedback(print_msg, allowable_actions)
    #     else:
    #         get_ai_feedback(self)
    #
    #     return feedback
    def get_player_tag(self):
        return "Player " + str(self.player_id) + " (" + self.name + ")"

    def get_player_feedback(self):
        """ This function should get overwritten by inheritance"""
        raise NotImplementedError()

    def generic_selection(self, action_space, player_phase_set, msg):
        """ Used by the custom action functions.
              Sets action_space, player phase, and uses inherited get_player_feedback function
              to get action from Bot or Human"""
        self.action_space = action_space
        self.player_state = player_phase_set
        player_choice = self.get_player_feedback()
        game_log.info(self.get_player_tag() + " " + msg + ": " + str(player_choice))

        return player_choice

    def select_initial_army_placement(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.INITIAL_ARMY_PLACEMENT, "Initial army placement")

    def select_initial_army_fortification(self, action_space):
        return self.generic_selection(
            action_space, PlayerPhases.INITIAL_ARMY_FORTIFICATION, "Initial army fortification"
        )

    def select_card_decision(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_CARD_CHECK, "Selects to use cards")

    def select_cards_to_use(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_CARD_PICK, "Selects card to use")

    def place_new_armies(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_PLACE_NEW_ARMIES, "Places new army in")

    def select_attack_from(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_ATTACKING_FROM, "Attacks from")

    def select_attack_to(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_ATTACKING_TO, "Attacking")

    def select_fortification_from(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_FORTIFICATION_FROM, "Fortifies from")

    def select_fortification_to(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_FORTIFICATION_TO, "Fortifying")

    def check_player_can_use_cards(self):
        if len(card_types) >= 3:
            # Need at least 3 cards to be able to cash cards in
            card_types = [card for card in self.cards]
        else:
            return False


=======

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
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0

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


<<<<<<< HEAD
class Human(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name):
        super().__init__(player_id, name)
        self.human = True
        self.bot_type = None
        # self.initialize_player(player_id, name, False)

    def get_human_feedback(self, print_msg) -> int:
        """ Human version of this function checks player state, prints custom message, collects desired feedback"""
        self.action_space = [str(i) for i in self.action_space]
        while True:
            print(self.get_player_tag() + " " + print_msg)
            print("Allowable actions: " + str(self.action_space))
            attempt = input()
            if attempt in self.action_space:
                # TODO implement repeat action strategy (ie, attack 10 times.  If player_state remains consistent then keep trying action, stop when one gets rejected.)
                return int(attempt)  # Selection should always be a player_id, territory_id, card_id, or card_use(y/n) (ie an int)
            elif attempt == "r":
                # r selects random element from allowable_actions
                return random.choice(self.action_space)
            elif attempt == "q":
                print("You have selected to quit game, are you sure you want to quit game? (y/n)")
                quit_confirm = input()
                if quit_confirm.lower() == "y":
                    game_log.info(self.get_player_tag() + " has elected to quit game")
                    # TODO implement game quit method
                else:
                    print("Resuming game")

            else:
                print("Invalid selection, input again")

    def get_player_feedback(self):
        if self.player_state == PlayerPhases.INITIAL_ARMY_PLACEMENT:
            print_msg = "Select an army placement"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.INITIAL_ARMY_FORTIFICATION:
            print_msg = "Select an army placement (fortification)"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_CARD_CHECK:
            print_msg = "Would you like to exchange cards for armies?"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_PLACE_NEW_ARMIES:
            print_msg = "Select an army placement"
            return self.get_human_feedback(print_msg)

        # elif game_state == PlayerPhases.PLAYER_ATTACKING: #This value should not be needed
        #     print_msg = "Select a country to attack"
        #     return self.get_human_feedback(print_msg)

        # elif game_state == PlayerPhases.PLAYER_FORTIFICATION: #This value should not be needed
        #     print_msg = "Select an army placement"
        #     return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_ATTACKING_FROM:
            print_msg = "Select a territory to attack from"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_ATTACKING_TO:
            print_msg = "Select a territory to attack"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_FORTIFICATION_FROM:
            print_msg = "Select a territory to fortify from"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_FORTIFICATION_TO:
            print_msg = "Select a territory to fortify to"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_CARD_PICK:
            print_msg = "Select a card"
            return self.get_human_feedback(print_msg)

        else:
            game_log.error("Invalid player state selected: " + str(self.player_state) + " (player_state)")
            raise ValueError


class Bot(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name, bot_type):
        super().__init__(player_id, name)
        self.human = False
        self.bot_type = bot_type


    def get_player_feedback(self):
        return random.choice(self.action_space)

    # def get_player_feedback(self):
    #     if self.player_state == PlayerPhases.INITIAL_ARMY_PLACEMENT:
    #         pass
    #     elif self.player_state == PlayerPhases.INITIAL_ARMY_FORTIFICATION:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_CARD_CHECK:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_PLACE_NEW_ARMIES:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_ATTACKING:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_FORTIFICATION:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_ATTACKING_FROM:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_ATTACKING_TO:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_FORTIFICATION_FROM:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_FORTIFICATION_TO:
    #         pass
    #     elif self.player_state == PlayerPhases.PLAYER_CARD_PICK:
    #         pass
    #     else:
    #         pass
=======
class Bot(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name, bot_type):
        super().__init__(player_id, name, bot_type)
        self.bot_type = bot_type  # TODO clean up initialization of bot
        self.initialize_player(player_id, name, False)

    def get_action(self, game_state):
        if game_state == PlayerPhases.INITIAL_ARMY_PLACEMENT:
            pass
        elif game_state == PlayerPhases.INITIAL_ARMY_FORTIFICATION:
            pass
        elif game_state == PlayerPhases.PLAYER_CARD_CHECK:
            pass
        elif game_state == PlayerPhases.PLAYER_PLACE_NEW_ARMIES:
            pass
        elif game_state == PlayerPhases.PLAYER_ATTACKING:
            pass
        elif game_state == PlayerPhases.PLAYER_FORTIFICATION:
            pass
        elif game_state == PlayerPhases.PLAYER_ATTACKING_FROM:
            pass
        elif game_state == PlayerPhases.PLAYER_ATTACKING_TO:
            pass
        elif game_state == PlayerPhases.PLAYER_FORTIFICATION_FROM:
            self.select_fortification_from()
        elif game_state == PlayerPhases.PLAYER_FORTIFICATION_TO:
            self.select_fortification_to()
        elif game_state == PlayerPhases.PLAYER_CARD_PICK:
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
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0


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
<<<<<<< HEAD
        # self.options["num_human_players"] = 3  # Case for a human game
        # self.options["computer_ai"] = []  # Case for a human game

        self.options["num_human_players"] = 0  # Case for a bot game
        self.options["computer_ai"] = ["random_ai", "random_ai", "random_ai"]  # Case for a bot game

=======
        self.options["num_human_players"] = 0
        self.options["computer_ai"] = ["random_ai", "random_ai", "random_ai"]
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0
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
<<<<<<< HEAD
        players = [Human(i, None) for i in range(self.num_human_players)]
=======
        players = [Player(i, None) for i in range(self.num_human_players)]
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0
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
<<<<<<< HEAD
                # player_choice = player.get_player_feedback(player_message, self.current_game_action_space)
                player_choice = player.select_initial_army_placement(self.current_game_action_space)
=======
                player_choice = player.get_player_feedback(player_message, self.current_game_action_space)
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0
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
<<<<<<< HEAD
                    selected_territory_id = player.select_initial_army_fortification(self.current_game_action_space)
                    self.adjust_player_army_reserve(player.player_id, -1)
                    self.adjust_territory_army_number(int(selected_territory_id), 1, addition_mode=True)

                self.calculate_game_army_reserves()
                if self.game_army_reserves <= 0:
                    self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES

    def play_player_turn(self, player):
        self.game_phase = GamePhases.PLAYER_CARD_CHECK
        player.player_state = PlayerPhases.PLAYER_CARD_CHECK
        player.check_player_can_use_cards()
        # CONTINUE HERE
        player.player_state = PlayerPhases.PLAYER_CARD_PICK

=======
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
>>>>>>> a25198eaf996849e9d24cb0522226ea29e39b7e0

        self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES

        self.game_phase = GamePhases.PLAYER_ATTACKING

        self.game_phase = GamePhases.PLAYER_FORTIFICATION


if __name__ == "__main__":
    game_log.info("Initialize Session")

    game = Game()

    while not game.game_over:
        game.play()

        game.game_over = True
