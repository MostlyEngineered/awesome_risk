# Risk game designed for AI

## Ruleset

Rules are designed on the original Risk Game, but planning on having a few different configurations that can be callable from a config file.  The idea is to make any level of AI automation programmable and abilities to skip the corner cases that almost never come up (like attacking with less than maximal force).

## OpenAI Gym
This will be turned into an open AI environment that will be configurable.

## Bots
Each player gets a player_state and an action_space.  Player_state is an enum that describes what kind of action the player is deciding.  Action_space is continually updated based on the context of the player/board (any of these actions can be chosen).
Bot behavior will be created by overriding the virtual get_player_feedback function (Player class should never be instantiated, only Humans or Bots based on the Bot Template).


## Usage
Current usage is just running game.py (no argparse or config yet so configuration is just changing the dictionary in the main loop)

#Credits
Map and some plotting used from https://github.com/godatadriven/risk-analysis/
