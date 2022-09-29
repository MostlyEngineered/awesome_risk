import random


def roll_dice(num_dice):
    """ roll number of dice """
    return [random.randint(1, 6) for x in range(num_dice)]


def resolve_combat(num_attack_dice, num_defense_dice):
    """ resolve combat
        rules: pairs are compared sequentially, defense wins ties
        return tuple of army losses (attacker losses, defender losses)"""
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
    return tuple(attack_losses, defense_losses)


def attack_dice_wins(attack_pips, defense_pips):
    """ compare pair of dice, defense wins ties"""
    return attack_pips > defense_pips


if __name__ == "__main__":
    resolve_combat(3, 2)
