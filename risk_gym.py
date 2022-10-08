from collections import deque
import numpy as np

import gym
from gym import error, spaces
from gym.error import DependencyNotInstalled
from gym.utils import EzPickle
from game import Game
from logger_format import get_logger
import numpy as np
import definitions
from player import calculate_territory_bonus, base_army_rate

game_log = get_logger("GameLog", file_name="game_log.txt", logging_level="info", clear_previous_logs=True)

gym_settings = {"gym_bot_position": 0}


def calculate_max_army_rate():
    total_num_territories = len(definitions.territory_names)
    max_territory_bonus = calculate_territory_bonus(total_num_territories)
    max_continent_bonus = sum(definitions.continent_bonuses.values())

    maximum_army_bonus = max_territory_bonus + max_continent_bonus


class RiskGym(gym.Env, EzPickle):

    # create a dedicated random number generator for the environment
    np_random = np.random.RandomState()

    max_army_rate = calculate_max_army_rate()
    army_rate_percentage = 0
    previous_army_rate_percentage = 0

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

    options["num_human_players"] = 0  # Gym environment always sets human players to 0
    game = Game(options)
    gym_player = game.get_player(gym_settings["gym_bot_position"])
    self.action_space = (
        gym_player.action_space
    )  # TODO gym_player.action_space should probably just be passed as the action space
    # Initialize all players here?
    # self.action_space = None  # Direct this at the player action space

    def reset(self, seed=None):
        # Manage seed
        self.seed(seed)

        self.game.game_over = True

        return self.env.reset(seed=seed, options=options, return_info=return_info)

    def step(self, action=None):  # TODO how does the action work when the space is not constant
        pass

    # game.play() #run game

    def reward(self, previous_reward=None, full_game_point=True):
        """Calculate reward based on army bonus, normalize to full bonus being worth 1 game.
        previous_reward: Subtract previous reward from current reward state (None will skip subtraction).
        full_game_point: If this is True then winning the game will get a full point reward
        """

        self.army_rate_percentage = (self.gym_player.army_rate - base_army_rate) / self.max_army_rate

        # TODO Check if env_player has won

        if previous_reward:
            gym_reward = army_rate_percentage - previous_reward
        else:
            gym_reward = army_rate_percentage

        return gym_reward

    def seed(self, seed=None):
        """
        Set the seed for this environment's random number generator.
        Returns:
            list<bigint>: Returns the list of seeds used in this env's random
              number generators. The first value in the list should be the
              "main" seed, or the value which a reproducer should pass to
              'seed'. Often, the main seed equals the provided 'seed', but
              this won't be true if seed=None, for example.
        """
        # if there is no seed, return an empty list
        if seed is None:
            return []
        # set the random number seed for the NumPy random number generator
        self.np_random.seed(seed)
        # return the list of seeds used by RNG(s) in the environment
        return [seed]

    def step(self, action):
        self.game.game_step()  # TODO this needs to advance a few game steps to get back to the gym_player's turn (number of game_steps will change when players are eliminated)


# class ConcatObs(gym.Wrapper):
#     def __init__(self, env, k):
#         gym.Wrapper.__init__(self, env)
#         self.k = k
#         self.frames = deque([], maxlen=k)
#         shp = env.observation_space.shape
#         self.observation_space = \
#             spaces.Box(low=0, high=255, shape=((k,) + shp), dtype=env.observation_space.dtype)
#
#
# def reset(self):
#     ob = self.env.reset()
#     for _ in range(self.k):
#         self.frames.append(ob)
#     return self._get_ob()
#
# def step(self, action):
#     ob, reward, done, info = self.env.step(action)
#     self.frames.append(ob)
#     return self._get_ob(), reward, done, info
#
# def _get_ob(self):
#     return np.array(self.frames)

if __name__ == "__main__":
    risk_gym = RiskGym()

    while not risk_gym.game.game_over:
        action = risk_gym.action_space.sample()
        n_state, reward, done, info = risk_gym.step(action)
        score += reward
