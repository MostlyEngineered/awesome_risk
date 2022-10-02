import random

import numpy as np

import definitions
from definitions import generate_random_name, PlayerPhases, CardPhases, CardType

# from game import game_log, program_log
from logger_format import get_logger

game_log = get_logger("GameLog", file_name="game_log.txt", logging_level="info")
program_log = get_logger("ProgramLog", file_name="program_errors.txt", logging_level="error")


class Player:
    """ Player class does not get instantiated as it will be missing a feedback option.  Instantiate a bot or a human."""

    def __init__(self, player_id, name) -> object:
        self.human = True

        # TODO organize folder for bots to allow easier selection

        if name is None:
            self.name = generate_random_name()
        else:
            self.name = name

        self.player_id = player_id
        self.cards = []
        self.card_usage_status = None
        self.card_strategies = None
        self.received_bonus_army_this_turn = False

        self.continents_owned = []
        self.territories_owned = []
        self.army_reserve = 0
        self.action_space = None
        self.player_state = None  # Update from PlayerState Enum
        self.can_attack = []
        self.can_attack_from = []
        self.territory_claimed_this_turn = False

    def get_player_tag(self):
        return "Player " + str(self.player_id) + " (" + self.name + ")"

    def get_player_feedback(self):
        """ This function should get overwritten by inheritance"""
        raise NotImplementedError()

    def generic_selection(self, action_space, player_phase_set, msg):
        """ Used by the custom action functions.
              Sets action_space, player phase, and uses inherited get_player_feedback function
              to get action from Bot or Human

              Note: checks if action_space is single element and will execute that element"""
        self.action_space = action_space
        self.player_state = player_phase_set
        if len(self.action_space) == 1:
            game_log.info("Only one choice, autoselecting")
            player_choice = action_space[0]
        elif len(self.action_space) == 0:
            program_log.error("Invalid action space: action space is 0")
            raise KeyError
        else:
            # Normal case
            player_choice = self.get_player_feedback()

        game_log.info(self.get_player_tag() + " " + msg + ": " + str(player_choice))

        return player_choice

    def select_initial_army_placement(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.INITIAL_ARMY_PLACEMENT, "Initial army placement")

    def select_initial_army_fortification(self, action_space):
        return self.generic_selection(
            action_space, PlayerPhases.INITIAL_ARMY_FORTIFICATION, "Initial army fortification"
        )

    def select_card_decision(self, action_space=[1, 0]):
        """ Decide if cards should be turned in (happens if hand is more than 3)"""
        return self.generic_selection(action_space, PlayerPhases.PLAYER_CARD_CHECK, "Selects to use cards")

    def select_cards_to_use(self, action_space):
        """ Decide which card to turn in (happens 3 times after card_decision=y or forced to play cards)"""
        return self.generic_selection(action_space, PlayerPhases.PLAYER_CARD_PICK, "Selects card to use")

    def place_new_armies(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_PLACE_NEW_ARMIES, "Places new army in")

    def select_attack_from(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_ATTACKING_FROM, "Attacks from")

    def select_attack_with(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_ATTACKING_WITH, "Attacks with how many armies")

    def select_attack_to(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_ATTACKING_TO, "Attacking")

    def select_attack_move_post_win(self, action_space):
        return self.generic_selection(
            action_space, PlayerPhases.PLAYER_MOVING_POST_WIN, "Move how many armies into new territory?"
        )

    def select_fortification_from(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_FORTIFICATION_FROM, "Fortifies from")

    def select_fortification_to(self, action_space):
        return self.generic_selection(action_space, PlayerPhases.PLAYER_FORTIFICATION_TO, "Fortifying")

    def check_player_can_use_cards(self):
        """ Check if player can or must use cards at start of turn"""
        # TODO this is failing picking up MIX with wilds with card_1 = wild
        if len(self.cards) >= 3:
            # Need at least 3 cards to be able to cash cards in
            card_types = [card.card_type for card in self.cards]
            card_hand = {}
            card_hand[CardType.WILD] = 0
            card_hand[CardType.INFANTRY] = 0
            card_hand[CardType.CAVALRY] = 0
            card_hand[CardType.ARTILLERY] = 0

            for card in card_types:
                card_hand[card] += 1

            num_types = 0
            for card_key in card_hand.keys():
                if (card_hand[card_key] >= 1) and not (card_key == CardType.WILD):
                    num_types += 1

            valid_card_strategies = {}
            self.card_usage_status = CardPhases.PLAYER_CANT_USE_CARDS
            if (card_hand[CardType.INFANTRY] + card_hand[CardType.WILD]) >= 3:
                valid_card_strategies[CardType.INFANTRY] = 1
                self.card_usage_status = CardPhases.PLAYER_CAN_USE_CARDS
            if (card_hand[CardType.CAVALRY] + card_hand[CardType.WILD]) >= 3:
                valid_card_strategies[CardType.CAVALRY] = 1
                self.card_usage_status = CardPhases.PLAYER_CAN_USE_CARDS
            if (card_hand[CardType.ARTILLERY] + card_hand[CardType.WILD]) >= 3:
                valid_card_strategies[CardType.ARTILLERY] = 1
                self.card_usage_status = CardPhases.PLAYER_CAN_USE_CARDS
            if (num_types + card_hand[CardType.WILD]) >= 3:
                valid_card_strategies["MIX"] = 1
                self.card_usage_status = CardPhases.PLAYER_CAN_USE_CARDS

            if len(self.cards) >= 5:
                self.card_usage_status = CardPhases.PLAYER_MUST_USE_CARDS

            return valid_card_strategies

            if card_hand[CardType.WILD] >= 1:
                print("Debugging here")

        else:
            self.card_usage_status = CardPhases.PLAYER_CANT_USE_CARDS
            return None

    def new_round_reserve_increase(self):
        continent_bonus = 0
        territory_bonus = int(np.floor(len(self.territories_owned) / 3))
        if territory_bonus < 3:
            territory_bonus = 3

        for continent in self.continents_owned:
            continent_bonus += definitions.continent_bonuses[continent]

        self.army_reserve = territory_bonus + continent_bonus
        game_log.info(self.get_player_tag() + " New turn bonus armies: " + str(self.army_reserve))

    def can_attack_to_from(self):
        territories_with_two = [
            territory.territory_id for territory in self.territories_owned if territory.num_armies >= 2
        ]

        player_id = self.player_id
        # Countries that connect to countries that have at least 2 armies
        can_attack = set()
        can_attack_from = set({-1})  # -1 corresponds to passing attack and will end attack phase
        for territory_id in territories_with_two:
            connected_territories = definitions.territory_neighbors[territory_id]
            valid_connections = set(connected_territories).difference(
                self.territory_ids
            )  # remove self-owned territories
            can_attack = can_attack.union(valid_connections)

            if len(valid_connections) > 0:
                # Needs to have at least one valid connection to attack from
                can_attack_from = can_attack_from.union(set({territory_id}))

        self.can_attack = list(can_attack)
        self.can_attack_from = list(can_attack_from)

    def can_attack_to(self, territory_from_id):
        connected_territories = definitions.territory_neighbors[territory_from_id]
        valid_connections = set(connected_territories).difference(self.territory_ids)  # remove self-owned territories
        return list(valid_connections)

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
            if attempt == "e":
                # Convert e (end) to -1 that will reside in some action spaces
                attempt = "-1"

            if attempt in self.action_space:
                # TODO implement repeat action strategy (ie, attack 10 times.  If player_state remains consistent then keep trying action, stop when one gets rejected.)
                return int(
                    attempt
                )  # Selection should always be a player_id, territory_id, card_id, or card_use(y/n) (ie an int)
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
            print_msg = "Would you like to exchange cards for armies (Y/N, 1/0)?"
            return self.get_human_feedback(print_msg)

        elif self.player_state == PlayerPhases.PLAYER_PLACE_NEW_ARMIES:
            print_msg = "Select an army placement"
            return self.get_human_feedback(print_msg)

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
        if self.player_state == PlayerPhases.PLAYER_ATTACKING_FROM:
            if len(self.action_space) > 1:  # Berzerker mode
                try:
                    self.action_space.pop(self.action_space.index(-1))  # Remove not attacking
                    return random.choice(self.action_space)
                except ValueError:
                    program_log("illegal op")
            if self.action_space == [-1]:
                return self.action_space[0]

        if self.player_state == PlayerPhases.PLAYER_ATTACKING_WITH:
            if 3 in self.action_space:
                return 3
            elif 2 in self.action_space:
                return 2


        return random.choice(self.action_space)

class BerzerkBot(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name, bot_type):
        super().__init__(player_id, name)
        self.human = False
        self.bot_type = bot_type

    def get_player_feedback(self):
        if self.player_state == PlayerPhases.PLAYER_ATTACKING_FROM:
            if len(self.action_space) > 1:  # Berzerker mode
                try:
                    self.action_space.pop(self.action_space.index(-1))  # Remove not attacking
                    return random.choice(self.action_space)
                except ValueError:
                    program_log("illegal op")
            if self.action_space == [-1]:
                return self.action_space[0]

        if self.player_state == PlayerPhases.PLAYER_ATTACKING_WITH:
            if 3 in self.action_space:
                return 3
            elif 2 in self.action_space:
                return 2


        return random.choice(self.action_space)


class RandomBot(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name, bot_type):
        super().__init__(player_id, name)
        self.human = False
        self.bot_type = bot_type

    def get_player_feedback(self):
         return random.choice(self.action_space)


class PacifistBot(Player):
    """ Should implement method for bot to convert so that it is player 0 for training purposes"""

    def __init__(self, player_id, name, bot_type):
        super().__init__(player_id, name)
        self.human = False
        self.bot_type = bot_type

    def get_player_feedback(self):
        if self.player_state == PlayerPhases.PLAYER_ATTACKING_FROM:
            if len(self.action_space) > 1:  # Berzerker mode
                try:
                    return -1  # Never attack
                except ValueError:
                    program_log("illegal op")

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
