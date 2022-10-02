import definitions

# from world import CONNECT, AREAS, MAP, KEY
from logger_format import get_logger
# from player import Human, Bot, Player
from player import *  # Import all bots from player
from world import World
from definitions import PlayerPhases, GamePhases, CardPhases, CardType
import random
from combat import resolve_combat

game_log = get_logger("GameLog", file_name="game_log.txt", logging_level="info")
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
            self.territory = definitions.territory_names[self.territory_id]

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
    # TODO finish card implementation
    # TODO finish fortification phase implementation

    def __init__(self, game_options) -> object:
        self.game_options = game_options

        self.num_human_players = self.game_options["num_human_players"]

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
        self.current_game_action_space = []
        self.turn = 0

    def play(self):
        """ This is the basic game loop
            Start initial setup phase and repeat player turns until game finished
            Log winner at the end"""
        self.play_initial_army_placement()
        self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION
        self.play_initial_army_fortification()
        self.save_player_territories_owned()

        while not self.game_over:
            self.turn += 1  # increment turn number
            self.calculate_game_stats()
            for player in self.players:
                if player in self.players:  # Players can be eliminated out of list
                    self.play_player_turn(player)


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



    def calculate_game_stats(self):
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
        # TODO make sure player_state is accurate through this process
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
            self.player_claims_cards(player)
            player.card_usage_status == CardPhases.PLAYER_CANT_USE_CARDS


    def player_claims_cards(self, player):
        """ Player is cashing in cards, consult strategies and cash in cards.
            This function is single cash in, repeat as necessary"""
        card_1 = self.pick_first_card(player)
        card_2 = self.pick_second_card(player, card_1)
        card_3 = self.pick_third_card(player, card_1, card_2)

        if not player.received_bonus_army_this_turn:
            bonus_options = [card.territory_id for card in [card_1, card_2, card_3] if card.territory_id in player.territories_owned]
            if bonus_options:
                bonus_choice = random.choice(bonus_options)  # TODO This should be a choice that the user makes (and can be a pass)
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

        selected_card_id = player.select_cards_to_use(action_space)
        return player_hand[selected_card_id]

    def pick_second_card(self, player, card_1):
        """ Pick card that is consistent with strategy, but 1 card can work for mix or single type strategy"""
        strategies = player.card_strategies
        player_hand = player.cards
        action_space = list()

        valid_cards = [card for card in player_hand if (card.card_type is CardType.WILD) and (card != card)]  # WILD always valid

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

        action_space = [player_hand.index(card) for card in player_hand if card in valid_cards]

        selected_card_id = player.select_cards_to_use(action_space)
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
            print("Debugging here")

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
        player.can_attack_to_from()  # Update player attack to/from lists
        while len(player.can_attack_from) > 0:
            player.player_state = PlayerPhases.PLAYER_ATTACKING_FROM
            selected_territory_attack_from = player.select_attack_from(player.can_attack_from)
            if selected_territory_attack_from == -1:
                game_log.info("Ending attack phase")
                break
            player.player_state = PlayerPhases.PLAYER_ATTACKING_WITH
            selected_armies_attack_with = player.select_attack_with(
                list(range(1, self.world.territories[selected_territory_attack_from].max_attack_with() + 1))
            )
            player.player_state = PlayerPhases.PLAYER_ATTACKING_TO
            selected_territory_to_attack = player.select_attack_to(player.can_attack_to(selected_territory_attack_from))
            self.resolve_attack(
                selected_territory_attack_from, selected_territory_to_attack, selected_armies_attack_with, player
            )
            player.can_attack_to_from()  # Update attack abilities after combat

    def play_fortification_phase(self, player):
        pass

    def deal_card_to_player(self, player):
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
        try:
            player_index = self.players.index(player_id)
        except ValueError:
            print('Debugging excpet')  # TODO figure this error out
            raise ValueError
        player = self.players[player_index]
        return player

    def get_allowable_initial_fortifications(self, player_id):
        return [territory.territory_id for territory in self.world.territories if territory.owner_id == player_id]

    def player_select_initial_placements(self):
        while not self.world.world_occupied:
            for player in self.players:
                player_message = "Player " + str(player.player_id) + " (" + player.name + "): Input country desired"
                self.current_game_action_space = [str(i) for i in self.world.allowable_placement_countries()]

                player_choice = player.select_initial_army_placement(self.current_game_action_space)

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
                self.current_game_action_space = self.get_allowable_initial_fortifications(player.player_id)
                for placement in range(batch_size):
                    if player.army_reserve <= 0:
                        continue

                    selected_territory_id = player.select_initial_army_fortification(self.current_game_action_space)
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
            for i in range(len(self.get_player(defender_id).cards)):
                player.cards.append(self.get_player(defender_id).cards.pop())

            game_log.info(player.get_player_tag() + " has been eliminated")
            self.out_players.append(self.players.pop(defender_id))
            if len(self.players) <= 1:
                self.game_over = True


if __name__ == "__main__":
    game_log.info("Initialize Session")

    options = {"num_human_players": 0, "computer_ai": ["RandomBot", "PacifistBot", "PacifistBot"],
                    "autodeal_territories": False, "initial_army_placement_batch_size": 1,
                    "always_maximal_attack": True, "berzerker_mode": True}

    # self.options["num_human_players"] = 3  # Case for a human game
    # self.options["computer_ai"] = []  # Case for a human game

    # self.options["computer_ai"] = ["random_ai"]  # Case for a single bot game

    game = Game(options)

    game.play()
