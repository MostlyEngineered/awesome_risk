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
            "initial_army_placement_batch_size": 1,
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

    def game_step(self):
        """ This is the basic game loop
            For this to work with OpenAI gym the game must advance in steps to subsequent actions
            """

    def play(self):
        """ This is the basic game loop
            Start initial setup phase and repeat player turns until game finished
            Log winner at the end"""
        self.initialize_board()
        self.play_initial_army_placement()
        self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION
        self.play_initial_army_fortification()
        self.save_player_territories_owned()

        while not self.game_over:
            self.turn += 1  # increment turn number
            self.calculate_game_stats()
            for player in self.players:
                self.current_player = player
                if player in self.players:  # Players can be eliminated out of list
                    self.play_player_turn(player)

            if self.turn >= self.game_options["turn_limit"]:
                self.player_victory(draw=True)
                game_log.info("Draw declared by turn limit")

        game_log.info(self.players[0].get_player_tag() + " is the winner")

    def save_player_territories_owned(self):
        """ Save which territories are owned by whom (in Player objects)"""
        for player in self.players:
            player.territory_ids = []
            player.territories_owned = []
            player.continents_owned = []

        for territory in self.world.territories:
            player = self.get_player(territory.owner_id)
            player.territories_owned.append(territory)
            player.territory_ids.append(territory.territory_id)

        for continent in definitions.continent_territories.keys():
            match_territories = definitions.continent_territories[continent]

            if set(match_territories).issubset(set(player.territory_ids)):
                player.continents_owned.append(continent)
        self.plot_board()

    def initialize_board(self):
        if not self.game_options["headless"]:

            self.im = plt.imread(os.getcwd() + "/img/risk.png")
            plt.figure(figsize=(16, 24))
            _ = plt.imshow(self.im)

    def get_territory_names(self):
        return_str = str(territory_names).replace(", ", "\n")
        return_str = return_str.replace("{", "").replace("}", "").replace("'", "")
        return return_str

    def plot_board(self):
        """ Plot the board. """
        if not self.game_options["headless"]:
            plt.clf()
            plt.imshow(self.im)
            plt.text(1, 340, s=self.territory_names_str, verticalalignment="top", fontsize=8)
            self.plot_player_statistics()
            game_phase_str = "Turn: " + str(self.turn) + "\n" + self.game_phase.name
            if self.current_player is not None:
                game_phase_str = (
                    game_phase_str
                    + "\n"
                    + self.current_player.player_state.name
                    + "\n"
                    + self.current_player.get_player_tag()
                )
            plt.text(1860, 650, game_phase_str, verticalalignment="top", horizontalalignment="center", fontsize=9)
            for t in self.world.territories:
                self.plot_single(t.territory_id, t.owner_id, t.num_armies)
            plt.axis("off")
            plt.pause(0.02)

    def plot_player_statistics(self):

        x_start = 400
        y_start = 1350
        x_end = 1600

        x_placements = np.linspace(x_start, x_end, len(self.players) + 1)

        for i, player in enumerate(self.players):
            player_text = player.get_player_tag()
            player_text = player_text + ("\nRound Bonus: " + str(player.army_rate))
            player_text = player_text + ("\nTerritories: " + str(len(player.territories_owned)))
            player_text = player_text + ("\nContinents: " + str(len(player.continents_owned)))
            x_text = (x_placements[i] + x_placements[i + 1]) / 2
            plt.text(x_text, y_start, player_text, fontsize=9, verticalalignment="top", horizontalalignment="center")

    @staticmethod
    def plot_single(territory_id, player_id, armies):
        """
        Plot a single army dot.

        Args:
            territory_id (int): the id of the territory to plot,
            player_id (int): the player id of the owner,
            armies (int): the number of armies.
        """
        coor = territory_locations[territory_id]
        plt.scatter([coor[0] * 1.2], [coor[1] * 1.22], s=1250, c=definitions.player_colors[player_id])
        plt.text(
            coor[0] * 1.2,
            coor[1] * 1.22 + 25,
            s=str(armies),
            color="black" if definitions.player_colors[player_id] in ["yellow", "pink"] else "white",
            ha="center",
            size=30,
        )
        plt.text(
            coor[0] * 1.2,
            (coor[1] * 1.22 + 25) + 10,
            s=str(territory_id),
            color="black" if definitions.player_colors[player_id] in ["yellow", "pink"] else "white",
            ha="center",
            size=10,
        )

    def calculate_game_stats(self):
        """ Calculate game stats to report to log"""
        self.save_player_territories_owned()
        game_log.info("Turn " + str(self.turn) + ": ")
        army_count = self.count_armies()
        for player in self.players:
            game_log.info(
                player.get_player_tag()
                + ": has "
                + str(army_count[player.player_id])
                + " armies and "
                + str(len(player.territories_owned))
                + " territories"
            )

    def play_player_turn(self, player):
        """ Play a player's normal turn
            1) Calculate new army reserves
            2) Check if the player can/wants to/must play cards and resolve cards
            3) Place armies in players' territories
            4) Player attacks until finished attacking (selects -1)
            5) Player selects one fortification actions
            6) Recalculate statistics (this will eliminate finished players)"""

        # Calculate army reserve increase
        player.territory_claimed_this_turn = False  # Reset conquer flag
        player.received_bonus_army_this_turn = False  # Reset bonus army flag

        player.new_round_reserve_increase()

        self.game_phase = GamePhases.PLAYER_CARD_CHECK
        self.play_card_phase(player)

        self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES
        self.play_place_new_armies(player)

        self.game_phase = GamePhases.PLAYER_ATTACKING
        self.play_attack_phase(player)

        self.game_phase = GamePhases.PLAYER_FORTIFICATION
        self.play_fortification_phase(player)

        if player.territory_claimed_this_turn == True:
            self.deal_card_to_player(player)  # if player conquers, deal a card

        self.save_player_territories_owned()  # Recalculate to eliminate any players with no countries #TODO this can be eliminated once game can be run through to check

    def play_card_phase(self, player):
        """ Play card phase
            1) Calculate if cards can/must be redeemed
            2) If player can, ask if they want to redeem cards
            3) If redemption is selected, player chooses cards"""
        player.player_state = PlayerPhases.PLAYER_CARD_CHECK
        player.card_strategies = player.check_player_can_use_cards()

        if player.card_usage_status == CardPhases.PLAYER_CAN_USE_CARDS:
            player_uses_cards = player.select_card_decision()  # action space for card decision is always Y/N (1/0)

            if player_uses_cards:
                # If player chooses to use cards, send into select cards
                player.card_usage_status = CardPhases.PLAYER_MUST_USE_CARDS

        else:
            player_uses_cards = 0

        if player_uses_cards or (player.card_usage_status == CardPhases.PLAYER_MUST_USE_CARDS):
            # players can get enough for multiple exchanges if multiple players are eliminated
            player.player_state = PlayerPhases.PLAYER_CARD_PICK
            self.player_claims_cards(player)
            player.card_usage_status == CardPhases.PLAYER_CANT_USE_CARDS

    def player_claims_cards(self, player):
        """ Player is cashing in cards, consult strategies and cash in cards.
            This function is single cash in, repeat as necessary"""
        card_1 = self.pick_first_card(player)
        card_2 = self.pick_second_card(player, card_1)
        card_3 = self.pick_third_card(player, card_1, card_2)

        if not player.received_bonus_army_this_turn:
            bonus_options = [
                card.territory_id for card in [card_1, card_2, card_3] if card.territory_id in player.territories_owned
            ]
            if bonus_options:
                bonus_choice = random.choice(
                    bonus_options
                )  # TODO This should be a choice that the user makes (and can be a pass)
                self.world.territories[bonus_choice].num_armies += 2
                player.received_bonus_army_this_turn = True

        try:
            self.discard_pile.append(player.cards.pop(player.cards.index(card_1)))
            self.discard_pile.append(player.cards.pop(player.cards.index(card_2)))
            self.discard_pile.append(player.cards.pop(player.cards.index(card_3)))
        except ValueError:
            print("Debugging here")

        print(player.get_player_tag() + " cashed in cards for " + str(self.army_bonus))

        player.army_reserve += self.army_bonus
        self.army_bonus = calculate_next_army_bonus(self.army_bonus)

    def pick_first_card(self, player):
        """ Have user select card index in hand, return the selected card"""
        strategies = player.card_strategies
        player_hand = player.cards
        action_space = list()
        valid_cards = list()

        print("Player hand is: " + str(len(player.cards)))

        valid_cards.append([card for card in player_hand if card.card_type is CardType.WILD])  # WILD always valid

        if CardType.INFANTRY in strategies.keys():
            valid_cards.append([card for card in player_hand if card.card_type is CardType.INFANTRY])

        if CardType.CAVALRY in strategies.keys():
            valid_cards.append([card for card in player_hand if card.card_type is CardType.CAVALRY])

        if CardType.ARTILLERY in strategies.keys():
            valid_cards.append([card for card in player_hand if card.card_type is CardType.ARTILLERY])

        valid_cards = flatten_list(valid_cards)  # Flatten list and Eliminate duplicates
        for card in valid_cards:
            action_space.append(player_hand.index(card))

        if "MIX" in strategies.keys():
            # Allow any cards for first card if there's a mix strategy
            # This overwrites the action_space in this case
            action_space = list(range(len(player_hand)))

        if len(action_space) <= 0:
            print("Debugging comment, this will be an error")

        player.action_space = action_space
        selected_card_id = player.select_cards_to_use(player.action_space)
        return player_hand[selected_card_id]

    def pick_second_card(self, player, card_1):
        """ Pick card that is consistent with strategy, but 1 card can work for mix or single type strategy"""
        strategies = player.card_strategies
        player_hand = player.cards
        action_space = list()

        valid_cards = [
            card for card in player_hand if (card.card_type is CardType.WILD) and (card != card)
        ]  # WILD always valid

        for card in player_hand:
            if card == card_1:
                continue
            if CardType.INFANTRY in strategies.keys() and card.card_type == CardType.INFANTRY:
                valid_cards.append(card)
                continue
            if (CardType.CAVALRY in strategies.keys()) and card.card_type == CardType.CAVALRY:
                valid_cards.append(card)
                continue
            if CardType.ARTILLERY in strategies.keys() and card.card_type == CardType.ARTILLERY:
                valid_cards.append(card)
                continue
            if "MIX" in strategies.keys() and card.card_type != card_1.card_type:
                valid_cards.append(card)

        player.action_space = [player_hand.index(card) for card in player_hand if card in valid_cards]

        selected_card_id = player.select_cards_to_use(player.action_space)
        return player_hand[selected_card_id]

    def pick_third_card(self, player, card_1, card_2):
        """ Continue strategy, but since 2 cards have been picked there is only 1 valid strategy (unless there's a wild)"""
        player_hand = player.cards
        action_space = list()
        valid_cards = list()

        valid_cards.append([card for card in player_hand if card.card_type is CardType.WILD])  # WILD always valid
        if card_1.card_type == card_2.card_type:
            # Single type strategy, find only cards of this type
            strategy_type = card_1.card_type
        else:
            # Mix strategy, find the type that doesn't match
            all_types = set({CardType.INFANTRY, CardType.CAVALRY, CardType.ARTILLERY})
            cur_types = set({card_1.card_type, card_2.card_type})
            strategy_type = list(all_types.difference(cur_types))[0]

        valid_cards.append([card for card in player_hand if card.card_type is strategy_type])

        valid_cards = flatten_list(valid_cards)

        if card_1.card_type == CardType.WILD or card_2.card_type == CardType.WILD:
            valid_cards = player_hand

        for card in valid_cards:
            if (card != card_1) and (card != card_2):
                action_space.append(player_hand.index(card))

        if len(action_space) <= 0:
            print("Debugging here, this evaluates to False sometimes")

        player.action_space = action_space
        selected_card_id = player.select_cards_to_use(action_space)
        return player_hand[selected_card_id]

    def play_place_new_armies(self, player):
        player.player_state = PlayerPhases.PLAYER_PLACE_NEW_ARMIES
        while player.army_reserve > 0:
            # New armies have to be placed in territories the player owns
            selected_territory = player.place_new_armies(action_space=player.territory_ids)
            player.army_reserve -= 1
            self.world.territories[selected_territory].num_armies += 1

    def play_attack_phase(self, player):
        player.calculate_can_attack_to_from()  # Update player attack to/from lists
        while len(player.can_attack_from) > 0:
            player.player_state = PlayerPhases.PLAYER_ATTACKING_FROM
            player.action_space = player.can_attack_from
            selected_territory_attack_from = player.select_attack_from(player.action_space)
            if selected_territory_attack_from == -1:
                game_log.info("Ending attack phase")
                break
            player.player_state = PlayerPhases.PLAYER_ATTACKING_WITH
            player.action_space = list(
                range(1, self.world.territories[selected_territory_attack_from].max_attack_with() + 1)
            )
            selected_armies_attack_with = player.select_attack_with(player.action_space)

            player.player_state = PlayerPhases.PLAYER_ATTACKING_TO
            player.action_space = player.calculate_can_attack_to(selected_territory_attack_from)
            selected_territory_to_attack = player.select_attack_to(player.action_space)

            self.resolve_attack(
                selected_territory_attack_from, selected_territory_to_attack, selected_armies_attack_with, player
            )
            player.calculate_can_attack_to_from()  # Update attack abilities after combat

    def play_fortification_phase(self, player):
        """ Select fortification from, with, and to (in that order)"""
        player.action_space = player.calculate_can_fortify_from()
        fortify_from_territory_id = player.select_fortification_from(player.action_space)
        if fortify_from_territory_id == -1:
            game_log.info(player.get_player_tag() + " Skipping fortification")
            return

        print("Territory has: " + str(self.world.territories[fortify_from_territory_id].num_armies))
        available_armies = (
            self.world.territories[fortify_from_territory_id].num_armies - 1
        )  # 1 army must be left behind
        if self.game_options["fortification_limit"] is not None:
            if available_armies > self.game_options["fortification_limit"]:
                available_armies = self.game_options["fortification_limit"]

        player.action_space = list(range(1, available_armies + 1))  # Must fortify with at least 1 army
        selected_with_armies = player.select_fortification_with(player.action_space)

        friendly_neighbors = definitions.territory_neighbors[fortify_from_territory_id]
        owner_ids = [territory.territory_id for territory in player.territories_owned]
        fortifiable_neighbors = [territory_id for territory_id in friendly_neighbors if territory_id in owner_ids]
        player.action_space = fortifiable_neighbors
        fortify_to_territory_id = player.select_fortification_to(player.action_space)

        # Execute the fortification
        self.adjust_territory_army_number(fortify_from_territory_id, selected_with_armies * -1, addition_mode=True)
        self.adjust_territory_army_number(fortify_to_territory_id, selected_with_armies, addition_mode=True)

    def deal_card_to_player(self, player):
        if not self.game_options["disable_cards"]:  # if cards have been disabled, don't deal cards ever
            player.cards.append(self.card_deck.pop())
            if len(self.card_deck) <= 0:
                # reshuffle discard pile
                self.card_deck = self.discard_pile
                self.discard_pile = []
                random.shuffle(self.card_deck)

    def count_armies(self):
        army_count = {}
        for player in self.players:
            army_count[player.player_id] = 0

        for territory in self.world.territories:
            army_count[territory.owner_id] += territory.num_armies
        return army_count

    def calculate_game_army_reserves(self):
        """ Calculate if all army reserves have been placed"""
        self.game_army_reserves = sum([player.army_reserve for player in self.players])

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

        players = [Human(i, None) for i in range(self.num_human_players)]

        for comp_player in self.game_options["computer_ai"]:
            players = players + [eval(comp_player)(player_id=len(players), name=None, bot_type=comp_player)]
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
        for _ in range(3):
            try:
                player_index = self.players.index(player_id)
                player = self.players[player_index]
                return player

            except ValueError:
                program_log.error("This ValueError occurs but in debugger evaluates")  # TODO figure this error out
        raise ValueError

    def get_allowable_initial_fortifications(self, player_id):
        return [territory.territory_id for territory in self.world.territories if territory.owner_id == player_id]

    def player_select_initial_placements(self):
        while not self.world.world_occupied:
            for player in self.players:
                player_message = "Player " + str(player.player_id) + " (" + player.name + "): Input country desired"
                player.action_space = [str(i) for i in self.world.allowable_placement_countries()]

                player_choice = player.select_initial_army_placement(player.action_space)

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
        if self.game_options["autodeal_territories"]:
            self.autodeal_initial_placements()
        else:
            self.player_select_initial_placements()

    def play_initial_army_fortification(self):
        game_log.info("Start initial fortification")
        batch_size = self.game_options["initial_army_placement_batch_size"]
        while game.game_phase == GamePhases.INITIAL_ARMY_FORTIFICATION:
            for player in self.players:
                player.action_space = self.get_allowable_initial_fortifications(player.player_id)
                for placement in range(batch_size):
                    if player.army_reserve <= 0:
                        continue

                    selected_territory_id = player.select_initial_army_fortification(player.action_space)
                    self.adjust_player_army_reserve(player.player_id, -1)
                    self.adjust_territory_army_number(int(selected_territory_id), 1, addition_mode=True)

                self.calculate_game_army_reserves()
                if self.game_army_reserves <= 0:
                    self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES

    def resolve_attack(self, territory_from, territory_to, with_armies, player):
        defense_armies = self.world.territories[territory_to].num_armies
        if defense_armies > 2:
            defense_armies = 2
        attack_losses, defense_losses = resolve_combat(with_armies, defense_armies)
        self.world.territories[territory_from].num_armies -= attack_losses
        self.world.territories[territory_to].num_armies -= defense_losses

        if self.world.territories[territory_to].num_armies <= 0:
            # if no armies or negative armies, this territory has changed owners
            self.player_conquers_territory(attack_losses, player, territory_from, territory_to, with_armies)

    def player_conquers_territory(self, attack_losses, player, territory_from, territory_to, with_armies):
        player.territory_claimed_this_turn = True
        defender_id = self.world.territories[territory_to].owner_id
        defending_player = self.get_player(defender_id)
        is_defender_last_territory = len(self.get_player(defender_id).territories_owned) <= 1

        player.player_state = PlayerPhases.PLAYER_MOVING_POST_WIN
        game_log.info(player.get_player_tag() + " wins territory " + str(territory_to))
        min_moving_armies = with_armies - attack_losses
        max_moving_armies = self.world.territories[territory_from].num_armies - 1
        move_number = player.select_attack_move_post_win(list(range(min_moving_armies, max_moving_armies + 1)))

        self.world.change_territory_owner(territory_to, player.player_id, move_number)  # Change owner
        self.save_player_territories_owned()  # Recalculate territories owned after owner change
        game_log.info(player.get_player_tag() + " moves " + str(move_number) + " to new territory")

        if is_defender_last_territory:
            # Defender is eleminated, transfer cards to invader
            self.eliminate_player(player, defending_player)

    def eliminate_player(self, attacking_player, eliminated_player):
        defender_id = eliminated_player.player_id
        for i in range(len(eliminated_player.cards)):
            attacking_player.cards.append(
                self.get_player(defender_id).cards.pop()
            )  # TODO replace with player elimination method

        game_log.info(eliminated_player.get_player_tag() + " has been eliminated")
        defender_index = self.players.index(eliminated_player)
        try:
            self.out_players.append(self.players.pop(defender_index))
        except IndexError:
            program_log.error("player elimination error")
            raise IndexError
        if len(self.players) <= 1:
            self.player_victory()

    def player_victory(self, draw=False):
        total_x = 2000  # TODO replace these with dimensions of im
        total_y = 1400

        self.game_over = True
        if draw:
            player_text = "DRAW"
        else:
            player_text = self.players[0].get_player_tag() + "\nWINS"

            plt.text(
                total_x / 2.0,
                total_y / 2.0,
                player_text,
                fontsize=45,
                horizontalalignment="center",
                verticalalignment="center",
            )


if __name__ == "__main__":
    game_log.info("Initialize Session")

    options = {
        "num_human_players": 0,
        "computer_ai": ["BerzerkBot", "PacifistBot", "PacifistBot"],
        "autodeal_territories": False,
        "initial_army_placement_batch_size": 1,
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
        game.game_step()

