#!/usr/bin/env python

import argparse
import csv
import pprint
import random

POPULATION_SIZE = 100
GENERATIONS = 1
FITNESS = int(POPULATION_SIZE * 0.25)

NUM_TEAMS = 10
ROSTER_SIZE = dict(
    QB=1,
    WR=2,
    RB=2,
    TE=1,
    K=1,
    DEF=1,
)

AUCTION_BUDGET = 200
MAXIMUM_BID = 80

# Logging Levels
STANDARD = 0
INFO = 1
DETAIL = 2
DEBUG = 3

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='count', help='Display verbose output')
parser.add_argument('-y', '--year', action='store', help="Use previous year's score results")
args = parser.parse_args()

def log(log_level, *msgs, **kwargs):
    msg = ' '.join(map(str, msgs))
    if args.verbose >= log_level:
        if kwargs.get('no_newline', False):
            print msg,
        else:
            print msg


def read_data():
    draft_data = {}
    year = '-{}'.format(args.year) if args.year else ''
    for position in ROSTER_SIZE.keys():

        with open('data/{}{}.csv'.format(position, year), 'rb') as csvfile:
            player_reader = csv.DictReader(csvfile)
            draft_data[position] = []
            rank = 1

            for player in sorted(player_reader, key=lambda p: float(p['fpts']), reverse=True):
                log(DEBUG, '{}: {} {}'.format(rank, position, player['Player Name']))
                if rank > ROSTER_SIZE[position] * NUM_TEAMS: # XXX TODO: account for flex/bench
                    break

                player['rank'] = rank
                draft_data[position].append(player)
                rank += 1
    return draft_data


def get_random_pp_draft_budget():
    """pp stands for positional player"""
    # XXX refactor to base this off of get_random_pp_draft_order
    # XXX then use that order to allocate budget remaining
    budget_remaining = AUCTION_BUDGET
    pp_draft_budget = []
    pp_draft_order = []
    for position, count in ROSTER_SIZE.iteritems():
        pp_draft_order.extend([position for _ in range(count)])

    random.shuffle(pp_draft_order)
    for position in pp_draft_order:
        max_bid = budget_remaining - (sum(ROSTER_SIZE.values()) - len(pp_draft_budget) - 1)
        max_bid = min([max_bid, MAXIMUM_BID])
        position_budget = random.randint(1, max_bid)
        budget_remaining -= position_budget
        pp_draft_budget.append({'position': position, 'budget': position_budget, 'drafted': False})
    return sorted(pp_draft_budget, key=lambda p: p['budget'], reverse=True)


def draft(draft_data, draft_budgets):
    pick = 0
    drafted_positions = {p: 0 for p in ROSTER_SIZE.keys()}
    draft_results = [[] for _ in range(NUM_TEAMS)]

    # XXX could this just be one long array of positions?
    pps_remaining_by_team = [[] for _ in range(NUM_TEAMS)]
    for team in range(len(pps_remaining_by_team)):
        for position, count in ROSTER_SIZE.iteritems():
            pps_remaining_by_team[team].extend([position for _ in range(count)])
        random.shuffle(pps_remaining_by_team[team])

    for round_pick in range(sum(ROSTER_SIZE.values())):
        for team in range(len(pps_remaining_by_team)):
            position = pps_remaining_by_team[team][round_pick]
            player = draft_data[position][drafted_positions[position]]
            player['pick'] = pick
            player['position'] = position
            log(INFO, 'Pick {}: Team {} nominates {} {}'.format(pick, team, position, player['Player Name']))

            # auction off the player
            # XXX we don't need each team to nominate every pp. Instead,
            # XXX once teams have filled their roster, they should stop nominating players
            winning_team = team
            winning_bid = next((bid for bid in draft_budgets[team]
                               if bid['position'] == position and not bid['drafted']),
                               {'budget': 0})
            for bidding_team in range(len(draft_budgets)):
                bidding_team = (bidding_team + team) % len(draft_budgets)
                if team == bidding_team:
                    continue

                try:
                    team_bid = next(bid for bid in draft_budgets[bidding_team]
                                    if bid['position'] == position and not bid['drafted'])
                except StopIteration:
                    continue

                if team_bid['budget'] > winning_bid['budget']:
                    winning_team = bidding_team
                    winning_bid = team_bid

            player['value'] = winning_bid['budget']
            winning_bid['drafted'] = True
            draft_results[winning_team].append(player)

            drafted_positions[position] += 1
            pick += 1
            log(INFO, 'Pick {}: Team {} drafts {} {} for ${}'.format(pick, winning_team, position, player['Player Name'], winning_bid['budget']))

    return draft_results


def record_draft_results(draft_results):
    pass

def main():
    draft_data = read_data()

    draft_budgets = []
    for team in range(NUM_TEAMS):
        draft_budgets.append(get_random_pp_draft_budget())

    for team in range(len(draft_budgets)):
        draft_budget = draft_budgets[team]
        log(DETAIL, 'Team', team, 'budgets:')
        log(DETAIL, '\n'.join(['{}: {}'.format(b['position'], b['budget']) for b in draft_budget]))
        log(DETAIL, '')

    results = draft(draft_data, draft_budgets)

    record_draft_results(results)

if __name__ == '__main__':
    main()
