from collections import deque
import numpy as np

import gym
from gym import error, spaces
from gym.error import DependencyNotInstalled
from gym.utils import EzPickle
from game import Game
from logger_format import get_logger
import numpy as np

game_log = get_logger("GameLog", file_name="game_log.txt", logging_level="info", clear_previous_logs=True)

gym_settings = {
    "gym_bot_position": 0
}

class RiskGym(gym.Env, EzPickle):


    # create a dedicated random number generator for the environment
    np_random = np.random.RandomState()

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
    self.action_space = gym_player.action_space  # TODO gym_player.action_space should probably just be passed as the action space
    # Initialize all players here?
    # self.action_space = None  # Direct this at the player action space

    def reset(self, seed=None):
        # Manage seed
        self.seed(seed)

        self.game.game_over = True



        return self.env.reset(
            seed=seed,
            options=options,
            return_info=return_info
        )

    def step(self, action=None):  # TODO how does the action work when the space is not constant
        pass
    # game.play() #run game

    def reward(self):
        num_territories = self.gym_player.territories_owned
        continent_bonus = self.gym_player.continent_bonus
        territory_bonus = self.gym_player.territory_bonus

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
