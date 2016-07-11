#!/usr/bin/env python

import argparse
import csv
import pprint
import random

from collections import defaultdict

POPULATION_SIZE = 10000
GENERATIONS = 100
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

# Logging Levels
STANDARD = 0
INFO = 1
DETAIL = 2
DEBUG = 3

DRAFT_ORDERS_AGE = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

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
        log(DEBUG, 'ROUND ' + str(draft_round))
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
            log(DEBUG, 'Pick ' + str(pick) + ': ' + 'Team ' + str(team) + ' drafts ' + player['Player Name'])
        log(DEBUG, '')
    return draft_results


def record_draft_results(current_generation, draft_results):
    # sort results
    for team in range(len(draft_results)):
        team_results = draft_results[team]
        for draft_result in team_results:
            draft_orders_key = '-'.join([player['position'] for player in draft_result])
            DRAFT_ORDERS_AGE[team][draft_orders_key]['age'] += 1
            DRAFT_ORDERS_AGE[team][draft_orders_key]['total'] += sum([float(player['fpts']) for player in draft_result])
        team_results.sort(
            key=lambda players: DRAFT_ORDERS_AGE[team]['-'.join([player['position'] for player in players])]['total'] / DRAFT_ORDERS_AGE[team]['-'.join([player['position'] for player in players])]['age'],
            reverse=True
        )

    log(INFO, 'Generation', current_generation, 'Results')
    for team in range(len(draft_results)):
        log(INFO, 'Team', team, 'draft:')
        for draft_number in range(10):
            draft_result = draft_results[team][draft_number]
            display_orders = '-'.join([player['position'] for player in draft_result])
            log(INFO, ' ', sum([float(player['fpts']) for player in draft_result]), no_newline=True)
            log(INFO, '(' + display_orders + ')', no_newline=True)
            log(INFO, int(DRAFT_ORDERS_AGE[team][display_orders]['age']), DRAFT_ORDERS_AGE[team][display_orders]['total'] / DRAFT_ORDERS_AGE[team][display_orders]['age'])
            log(DETAIL, ' ', ', '.join([player['Player Name'] for player in draft_result]))
        log(INFO, '')


def spawn_next_generation(draft_results):
    # select the top fit team drafts
    fit_orders_by_team = [[] for _ in range(NUM_TEAMS)]
    for team in range(len(draft_results)):
        for draft_number in range(FITNESS):
            fit_orders = [player['position'] for player in draft_results[team][draft_number]]
            fit_orders_by_team[team].append(fit_orders)

            # mutate team drafts
            if random.random() < 0.10:
                i = random.randint(0, len(fit_orders)-2)
                fit_orders[i+1], fit_orders[i] = fit_orders[i], fit_orders[i+1]
                fit_orders_by_team[team].append(fit_orders)

    # make hybrid team drafts from fit parents

    # pair up top team drafts to make full draft for next generation
    next_gen_draft_orders = []
    # XXX not sure what to call this magic number... matings?
    for _ in range(int(POPULATION_SIZE * 0.75)):
        draft_orders = []
        for team_draft_orders in fit_orders_by_team:
            draft_orders.append(random.choice(team_draft_orders))
        next_gen_draft_orders.append(draft_orders)

    return next_gen_draft_orders


def get_sort_value(d):
    return d[1]['total'] / d[1]['age']


def main():
    draft_data = read_data()

    generation_draft_orders = []
    for generation in range(GENERATIONS):
        for _ in range(POPULATION_SIZE - len(generation_draft_orders)):
            draft_orders = []
            for team in range(NUM_TEAMS):
                draft_orders.append(get_random_pp_draft_order())
            generation_draft_orders.append(draft_orders)

        draft_results = [[] for _ in range(NUM_TEAMS)]
        for draft_orders in generation_draft_orders:
            results = draft(draft_data, draft_orders)
            for team in range(NUM_TEAMS):
                draft_results[team].append(results[team])

        record_draft_results(generation, draft_results)
        generation_draft_orders = spawn_next_generation(draft_results)

    for team, drafts in DRAFT_ORDERS_AGE.iteritems():
        print 'Summary for team', team, ':'
        sorted_orders_by_age = sorted(drafts.items(), key=lambda d: get_sort_value(d), reverse=True)
        for i in range(10):
            orders, orders_age = sorted_orders_by_age[i]
            print ' ', int(orders_age['age']), (orders_age['total'] / orders_age['age']), '(' + orders + ')'
        print


if __name__ == '__main__':
    main()
