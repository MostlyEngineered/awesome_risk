import random
from logger_format import get_logger

program_log = get_logger("ProgramLog", file_name="program_errors.txt", logging_level="error")


def roll_dice(num_dice):
    """ roll number of dice """
    return [random.randint(1, 6) for x in range(num_dice)]


def attack_dice_wins(attack_pips, defense_pips):
    """ compare pair of dice, defense wins ties"""
    return attack_pips > defense_pips


def resolve_combat(num_attack_dice, num_defense_dice):
    """ resolve combat
        rules: pairs are compared sequentially, defense wins ties
        return tuple of army losses (attacker losses, defender losses)"""

    if num_attack_dice > 3:
        program_log.error("illegal amount of attack dice")
        raise ValueError
    elif num_defense_dice > 2:
        program_log.error("illegal amount of defense dice")
        raise ValueError

    attack_dice = roll_dice(num_attack_dice)
    defense_dice = roll_dice(num_defense_dice)
    attack_dice.sort(reverse=True)
    defense_dice.sort(reverse=True)
    min_dice = min(num_attack_dice, num_defense_dice)
    attack_losses = 0
    defense_losses = 0
    for i in range(min_dice):
        if attack_dice_wins(attack_dice[i], defense_dice[i]):
            attack_losses += 1
        else:
            defense_losses += 1
    return attack_losses, defense_losses


if __name__ == "__main__":
    resolve_combat(3, 2)
