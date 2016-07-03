#!/usr/bin/env python

import csv
import pprint
import random

POPULATION_SIZE = 100000
GENERATIONS = 10
FITNESS = 500

NUM_TEAMS = 32
ROSTER_SIZE = dict(
    QB=1,
    WR=2,
    RB=2,
    TE=1,
    #K=1,
)

def read_data():
    draft_data = {}
    for position in ROSTER_SIZE.keys():
        with open('data/{}.csv'.format(position), 'rb') as csvfile:
            player_reader = csv.DictReader(csvfile)
            draft_data[position] = []
            rank = 1

            for player in player_reader:
                if rank > ROSTER_SIZE[position] * NUM_TEAMS: # XXX TODO: account for flex/bench
                    break

                player['rank'] = rank
                draft_data[position].append(player)
                rank += 1
    return draft_data


def get_random_pp_draft_order():
    """pp stands for positional player"""
    pp_draft_order = []
    for position, count in ROSTER_SIZE.iteritems():
        pp_draft_order.extend([position for _ in range(count)])

    random.shuffle(pp_draft_order)
    return pp_draft_order


def draft(draft_data, draft_orders):
    # now we get to do the draft
    pick = 0
    drafted_positions = {p: 0 for p in ROSTER_SIZE.keys()}
    draft_results = [[] for _ in range(NUM_TEAMS)]
    for draft_round in range(sum(ROSTER_SIZE.values())):
        # print 'ROUND', str(draft_round)
        for team in range(len(draft_orders)):
            if draft_round % 2 != 0:
                team = NUM_TEAMS - 1 - team

            position = draft_orders[team][draft_round]
            player = draft_data[position][drafted_positions[position]]
            player['pick'] = pick
            player['position'] = position
            draft_results[team].append(player)

            drafted_positions[position] += 1
            pick += 1
            # print 'Pick', str(pick) + ':', 'Team', str(team), 'drafts', player['Player Name']
        # print
    return draft_results


def spawn_next_generation(current_generation, draft_results):
    # process results
    for team_results in draft_results:
        team_results.sort(
            key=lambda players: sum([float(player['fpts']) for player in players]),
            reverse=True
        )

    print 'Generation', current_generation, 'Results'
    for team in range(len(draft_results)):
        print 'Team', team, 'draft:'
        for draft_number in range(10):
            draft_result = draft_results[team][draft_number]
            print ' ', sum([float(player['fpts']) for player in draft_result]),
            print '(' + '-'.join([player['position'] for player in draft_result]) + ')'
        print

    fit_orders_by_team = [[] for _ in range(NUM_TEAMS)]
    for team in range(len(draft_results)):
        for draft_number in range(FITNESS):
            fit_orders_by_team[team].append([player['position']
                                             for player in draft_results[team][draft_number]])

    next_gen_draft_orders = []
    for _ in range(1000): # XXX not sure what to call this magic number... matings?
        draft_orders = []
        for team_draft_orders in fit_orders_by_team:
            draft_orders.append(random.choice(team_draft_orders))
        #pprint.pprint(draft_orders)
        next_gen_draft_orders.append(draft_orders)

    return next_gen_draft_orders


def main():
    draft_data = read_data()

    generation_draft_orders = []
    for _ in range(POPULATION_SIZE):
        draft_orders = []
        for team in range(NUM_TEAMS):
            draft_orders.append(get_random_pp_draft_order())
        generation_draft_orders.append(draft_orders)

    for generation in range(GENERATIONS):
        draft_results = [[] for _ in range(NUM_TEAMS)]
        for draft_orders in generation_draft_orders:
            results = draft(draft_data, draft_orders)
            for team in range(NUM_TEAMS):
                draft_results[team].append(results[team])

        generation_draft_orders = spawn_next_generation(generation, draft_results)


if __name__ == '__main__':
    main()
