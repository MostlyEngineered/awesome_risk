from combat import *
from game import *
from definitions import *
import unittest
import random

random.seed(111111)


class TestCombat(unittest.TestCase):
    def test_roll_dice(self):
        """ roll number of dice """
        dice = roll_dice(100)
        for die in dice:
            self.assertGreaterEqual(die, 1)
            self.assertLessEqual(die, 6)

        for num_dice in range(1, 100):
            self.assertEqual(len(roll_dice(num_dice)), num_dice)

    def test_attack_dice_wins(self):
        self.assertTrue(attack_dice_wins(2, 1))
        self.assertFalse(attack_dice_wins(1, 1))
        self.assertFalse(attack_dice_wins(1, 2))

    # def test_random_seed(self):
    #     self.assertEqual(random.randint(1, 1000000), 719752)


class TestCards(unittest.TestCase):
    game_options = {
        "num_human_players": 0,
        "computer_ai": ["Bot", "Bot", "Bot"],
        "autodeal_territories": False,
        "initial_army_placement_batch_size": 1,
        "always_maximal_attack": True,
        "berzerker_mode": True,
    }
    game = None

    def setup_test_cards(self):
        # self.game_options = {"num_human_players": 0, "computer_ai": ["Bot", "Bot", "Bot"],
        #            "autodeal_territories": False, "initial_army_placement_batch_size": 1,
        #            "always_maximal_attack": True, "berzerker_mode": True}

        self.game = Game(self.game_options)
        self.game.card_deck.sort()

        self.botty = self.game.players[0]

    def card_turn_in(self, card_list):
        self.setup_test_cards()

        for card_id in card_list:
            self.botty.cards.append(self.game.card_deck[card_id])

        self.botty.card_strategies = self.botty.check_player_can_use_cards()
        self.game.player_claims_cards(self.botty)

    def check_card_turn_in(self, card_list):
        self.card_turn_in(card_list)
        self.assertEqual(self.botty.army_reserve, 4)  # One Card hand-in

    def check_card_turn_in_fails(self, card_list):
        with self.assertRaises(KeyError):
            self.card_turn_in(card_list)

    def test_basic_card_combinations(self):
        self.check_card_turn_in([0, 1, 9])  # Infantry, Artillery, Cavalry
        self.check_card_turn_in([0, 3, 4])  # Infantry, Infantry, Infantry
        self.check_card_turn_in([1, 2, 6])  # Artillery, Artillery, Artillery
        self.check_card_turn_in([9, 13, 14])  # Cavalry, Cavalry, Cavalry

    def test_bad_card_combinations(self):
        self.check_card_turn_in_fails([0, 13, 14])  # Infantry, Cavalry, Cavalry

    def test_wild_card_combinations(self):
        self.check_card_turn_in([0, 42, 43])  # Infantry, Wild, Wild
        self.check_card_turn_in([0, 42, 9])  # Infantry, Wild, Cavalry
        self.check_card_turn_in([0, 42, 1])  # Infantry, Wild, Artillery

        self.check_card_turn_in([0, 42, 43, 3, 4])  # Add cards to previous
        self.check_card_turn_in([0, 42, 9, 1])  # Add cards to previous
        self.check_card_turn_in([0, 42, 1, 9, 3, 4])  # Add cards to previous

    def test_run_game_to_end(self):
        options = {
            "num_human_players": 0,
            "computer_ai": ["BerzerkBot", "PacifistBot", "PacifistBot"],
            "autodeal_territories": False,
            "initial_army_placement_batch_size": 1,
            "always_maximal_attack": True,
            "berzerker_mode": True,
            "turn_limit": 300,
            "headless": True
            }  # At current skill level if game hasn't ended by 150 turns it's probably not ending

        # self.options["num_human_players"] = 3  # Case for a human game
        # self.options["computer_ai"] = []  # Case for a human game

        # self.options["computer_ai"] = ["random_ai"]  # Case for a single bot game
        cur_game = Game(options)

        cur_game.play()

if __name__ == "__main__":
    unittest.main()
