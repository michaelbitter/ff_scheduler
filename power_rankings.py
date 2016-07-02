#!/usr/bin/env python

"""
Baseball power rankings are calculated by adding the following four terms
together. To calculate a power ranking number, you need W-L record, streak,
and last 10 games record.

1. 90
2. ROUND( ( (WINNING_PCT) - 0.500 ) * 162 * 10/9 )
3. ( WINS_IN_LAST_10_GAMES - LOSSES_IN_LAST_10_GAMES )
4. ( +1 IF ON WINNING STREAK ELSE IF ON LOSING STREAK -1 ) *
   ROUND( ( (STREAK_LENGTH) - 1 ) / 2 )
"""

import argparse

def get_args():
    """Get some command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--record', required=True,
                        help='Win/Loss record of team specified as <Wins>-<Losses>')
    parser.add_argument('-s', '--streak', required=True,
                        help='Current streak of team specified as (W|L)\d+')
    parser.add_argument('-l', '--last', required=True,
                        help='Record over last 10 games specified as <Wins>-<Losses>')
    return parser


def calculate_power_ranking(wins, losses, is_winning_streak,
                            streak_length, recent_wins, recent_losses):
    """Calculate a power ranking number given inputs."""
    pred1 = 0
    pred2 = round( ( ((wins*1.0)/(wins+losses)) - 0.500 ) * 16 * 9 * 10/9 )
    pred3 = recent_wins - recent_losses
    streak_factor = 1 if is_winning_streak else -1
    pred4 = streak_factor * round( ( streak_length - 1 ) / 2.0 )
    print pred1, pred2, pred3, pred4
    return pred1 + pred2 + pred3 + pred4


def main():
    """Main entry point to the program."""
    args = get_args().parse_args()

    (wins, losses) = args.record.split('-')
    print wins, losses
    
    is_winning_streak = args.streak[0] == 'W'
    streak_length = args.streak[1:]
    print is_winning_streak, streak_length

    (recent_wins, recent_losses) = args.last.split('-')
    print recent_wins, recent_losses

    power_ranking = calculate_power_ranking(int(wins), int(losses), is_winning_streak,
                                            int(streak_length), int(recent_wins),
                                            int(recent_losses))
    print power_ranking
    
if __name__ == '__main__':
    main()
