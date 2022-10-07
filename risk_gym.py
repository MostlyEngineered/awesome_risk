from collections import deque
import numpy as np

import gym
from gym import error, spaces
from gym.error import DependencyNotInstalled
from gym.utils import EzPickle
from game import Game

class RiskGym(gym.Env, EzPickle):

    game_log.info("Initialize Session")

    options = {"num_human_players": 0, "computer_ai": ["BerzerkBot", "PacifistBot", "PacifistBot"],
                    "autodeal_territories": False, "initial_army_placement_batch_size": 1,
                    "always_maximal_attack": True, "berzerker_mode": True,
                    "turn_limit": 150, "headless": False}  # At current skill level if game hasn't ended by 150 turns it's probably not ending

    game = Game(options)




    #Initialize all players here?
    self.action_space = None  # Direct this at the player action space



    def reset(self):
        # Manage seed
        game.game_over = True

    # game.play() #run game



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