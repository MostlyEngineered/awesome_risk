import definitions

# from world import CONNECT, AREAS, MAP, KEY
from logger_format import get_logger
from player import Human, Bot, Player
from world import World
from definitions import PlayerPhases, GamePhases, CardPhases
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

        # self.options["num_human_players"] = 3  # Case for a human game
        # self.options["computer_ai"] = []  # Case for a human game

        self.options["num_human_players"] = 0  # Case for a bot game
        self.options["computer_ai"] = ["random_ai", "random_ai", "random_ai"]  # Case for a bot game
        # self.options["computer_ai"] = ["random_ai"]  # Case for a single bot game

        self.options["autodeal_territories"] = False  # Normal game set this to false
        self.options[
            "initial_army_placement_batch_size"
        ] = 1  # How many armies a player places at a time after initial country selection
        self.options["always_maximal_attack"] = True  # Game always attack with maximal force
        self.options["berzerker_mode"] = True  # Disable passing attacking

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
        self.turn = 0

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

        for player in self.players:
            if len(player.territories_owned) <= 0:
                game_log.info(player.get_player_tag() + " has been eliminated")
                player_game_index = self.players.index(player)
                self.out_players.append(self.players.pop(player_game_index))
                if len(self.players) <= 1:
                    self.game_over = True

    def count_armies(self):
        army_count = {}
        for player in self.players:
            army_count[player.player_id] = 0

        for territory in self.world.territories:
            army_count[territory.owner_id] += territory.num_armies
        return army_count

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

    def calculate_game_army_reserves(self):
        """ Calculate if all army reserves have been placed"""
        self.game_army_reserves = sum([player.army_reserve for player in self.players])

    def play(self):
        self.play_initial_army_placement()
        self.game_phase = GamePhases.INITIAL_ARMY_FORTIFICATION
        self.play_initial_army_fortification()

        while not self.game_over:
            self.turn += 1  # increment turn number
            self.calculate_game_stats()
            for player in self.players:
                if player in self.players:  # Players can be eliminated out of list
                    self.play_player_turn(player)

        game_log.info(self.players[0].get_player_tag() + " is the winner")

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

                    selected_territory_id = player.select_initial_army_fortification(self.current_game_action_space)
                    self.adjust_player_army_reserve(player.player_id, -1)
                    self.adjust_territory_army_number(int(selected_territory_id), 1, addition_mode=True)

                self.calculate_game_army_reserves()
                if self.game_army_reserves <= 0:
                    self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES

    def play_player_turn(self, player):

        # Calculate army reserve increase
        self.save_player_territories_owned()
        player.new_round_reserve_increase()

        self.game_phase = GamePhases.PLAYER_CARD_CHECK
        self.play_card_phase(player)

        self.game_phase = GamePhases.PLAYER_PLACE_NEW_ARMIES
        self.play_place_new_armies(player)

        self.game_phase = GamePhases.PLAYER_ATTACKING
        self.play_attack_phase(player)

        self.game_phase = GamePhases.PLAYER_FORTIFICATION
        self.play_fortification_phase(player)

        self.save_player_territories_owned()  # Recalculate to eliminate any players with no countries

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

    def resolve_attack(self, territory_from, territory_to, with_armies, player):
        defense_armies = self.world.territories[territory_to].num_armies
        if defense_armies > 2:
            defense_armies = 2
        attack_losses, defense_losses = resolve_combat(with_armies, defense_armies)
        self.world.territories[territory_from].num_armies -= attack_losses
        self.world.territories[territory_to].num_armies -= defense_losses

        if self.world.territories[territory_to].num_armies <= 0:
            # if no armies or negative armies, this territory has changed owners
            player.player_state = PlayerPhases.PLAYER_MOVING_POST_WIN
            game_log.info(player.get_player_tag() + " wins territory " + str(territory_to))
            min_moving_armies = with_armies - attack_losses
            max_moving_armies = self.world.territories[territory_from].num_armies - 1
            move_number = player.select_attack_move_post_win(list(range(min_moving_armies, max_moving_armies + 1)))
            self.world.change_territory_owner(territory_to, player.player_id, move_number)
            game_log.info(player.get_player_tag() + " moves " + str(move_number) + " to new territory")

    def play_fortification_phase(self, player):
        pass

    def play_place_new_armies(self, player):
        player.player_state = PlayerPhases.PLAYER_PLACE_NEW_ARMIES
        while player.army_reserve > 0:
            # New armies have to be placed in territories the player owns
            selected_territory = player.place_new_armies(action_space=player.territory_ids)
            player.army_reserve -= 1
            self.world.territories[selected_territory].num_armies += 1

    def play_card_phase(self, player):
        # TODO make sure player_state is accurate through this process
        player.player_state = PlayerPhases.PLAYER_CARD_CHECK
        player.check_player_can_use_cards()
        if player.card_usage_status == CardPhases.PLAYER_CAN_USE_CARDS:
            player_uses_cards = player.select_card_decision()  # action space for card decision is always Y/N (1/0)
        else:
            player_uses_cards = 0
        while player_uses_cards or (player.card_usage_status == CardPhases.PLAYER_MUST_USE_CARDS):
            # players can get enough for multiple exchanges if multiple players are eliminated
            for i in range(3):
                # TODO finish the card implementation
                select_card = player.select_card_decision()
                player.check_player_can_use_cards()
                player_uses_cards = 0
                if player.card_usage_status == CardPhases.PLAYER_CAN_USE_CARDS:
                    player_uses_cards = player.select_card_decision(
                        action_space=[]
                    )  # TODO Need to calculate action space
                if (not player_uses_cards) and (player.card_usage_status != CardPhases.PLAYER_MUST_USE_CARDS):
                    break


if __name__ == "__main__":
    game_log.info("Initialize Session")

    game = Game()

    game.play()
