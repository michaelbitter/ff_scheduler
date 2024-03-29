#!/usr/bin/env python

import argparse
import datetime
import copy
import csv
import pprint
import random

from collections import defaultdict
from multiprocessing import Pool

POPULATION_SIZE = 10000
GENERATIONS = 100
FITNESS = int(POPULATION_SIZE * 0.15) or 1

NUM_TEAMS = 10
ROSTER_SIZE = dict(
    QB=2,
    WR=4,
    RB=4,
    TE=1,
#    FLEX=4,
    K=1,
    DEF=1,
#    BENCH=3,
)

SCORING_SETTINGS = dict(
    QB=dict(
        fumble_lost=-2,
        passing_attempts=0,
        passing_completions=0,
        passing_int=-2,
        passing_td=6,
        passing_yards=0.05,
        rushing_attempts=0,
        rushing_td=6,
        rushing_yards=0.1,
    ),
    WR=dict(
        fumble_lost=-2,
        receiving_td=6,
        receiving_yards=0.1,
        receptions=0.5,
        rushing_attempts=0,
        rushing_td=6,
        rushing_yards=0.1,
    ),
    RB=dict(
        fumble_lost=-2,
        receiving_td=6,
        receiving_yards=0.1,
        receptions=0.5,
        rushing_attempts=0,
        rushing_td=6,
        rushing_yards=0.1,
    ),
    TE=dict(
        fumble_lost=-2,
        receiving_td=6,
        receiving_yards=0.1,
        receptions=0.5,
    ),
    K=dict(
        extra_point=1,
        fg=4,
        fg_attempt=0,
        #fg_miss=-2, # XXX figure out how to derive this # derived from total fg_attempts - total fgs
    ),
    DEF=dict(
        fumble_recovery=2,
        forced_fumble=1,
        interception=2,
        points_allowed=-0.065,
        sack=2,
        safety=4,
        td=8,
        yards_against=0,
    ),
)

AUCTION_BUDGET = 297
MAXIMUM_BID = 225

# Logging Levels
STANDARD = 0
INFO = 1
DETAIL = 2
DEBUG = 3

DRAFT_BUDGETS_AGE = defaultdict(lambda: defaultdict(float))
PLAYER_BUDGETS = defaultdict(lambda: defaultdict(list))

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='count', help='Display verbose output')
parser.add_argument('-y', '--year', action='store', help="Use previous year's score results")
args = parser.parse_args()

def log(log_level, *msgs, **kwargs):
    msg = ' '.join(map(str, msgs))
    display_level = args.verbose or 0
    if display_level >= log_level:
        if kwargs.get('no_newline', False):
            print(msg, end=' ')
        else:
            print(msg, flush=True)


def memoize(f):
    cache = {}
    def decorated_function(*args):
        if args in cache:
            return cache[args]
        else:
            cache[args] = f(*args)
            return cache[args]
    return decorated_function


@memoize
def read_data():
    draft_data = {}
    year = args.year if args.year else datetime.date.today().year
    for position in list(ROSTER_SIZE.keys()):
        log(DEBUG, 'Processing data/{}/{}.csv'.format(year, position))
        with open('data/{}/{}.csv'.format(year, position), 'r', encoding='utf8') as csvfile:
            player_reader = csv.DictReader(csvfile)
            players = []
            draft_data[position] = []
            rank = 1

            for player in player_reader:
                fpts = 0
                for action, score in SCORING_SETTINGS[position].items():
                    fpts += float(player[action].replace(',','')) * score
                player['fpts'] = _round(fpts)
                players.append(player)

            for player in sorted(players, key=lambda p: p['fpts'], reverse=True):
                log(DETAIL, '{}: {} {} ({})'.format(rank, position, player['Player Name'], player['fpts']))
                if rank > ROSTER_SIZE[position] * NUM_TEAMS: # XXX TODO: account for flex/bench
                    break

                player['rank'] = rank
                draft_data[position].append(player)
                rank += 1
    return draft_data


def _round(n, d=1):
    round_factor = 10.0 ** d
    return int(n * round_factor + 0.5) / round_factor


@memoize
def player_value_above_replacement():
    player_data = read_data()
    player_values = {}
    total_budget = NUM_TEAMS * AUCTION_BUDGET
    total_value = 0
    for position in list(player_data.keys()):
        replacement_index = NUM_TEAMS * ROSTER_SIZE[position] - 1
        replacement_value = float(player_data[position][replacement_index]['fpts'])
        log(DEBUG, 'Replacement', position, 'is', player_data[position][replacement_index]['Player Name'], 'with value', replacement_value)
        for player_info in player_data[position]:
            value_above_replacement = _round(player_info['fpts'] - replacement_value)
            player_values[player_info['Player Name']] = value_above_replacement
            total_value += value_above_replacement
    log(STANDARD, 'Point Cost is', _round(total_value/total_budget, 3), 'points per dollar (', _round(total_value), 'pts / $', total_budget, ')')
    return player_values


def distribute(additional_budget, draft_budget):
    draft_budget[0]['budget'] += additional_budget


def get_random_pp_draft_budget():
    """pp stands for positional player"""
    # XXX refactor to base this off of get_random_pp_draft_order
    # XXX then use that order to allocate budget remaining
    budget_remaining = AUCTION_BUDGET
    pp_draft_budget = []
    pp_draft_order = []
    for position, count in ROSTER_SIZE.items():
        pp_draft_order.extend([position for _ in range(count)])

    random.shuffle(pp_draft_order)
    for position in pp_draft_order:
        max_bid = budget_remaining - (sum(ROSTER_SIZE.values()) - len(pp_draft_budget) - 1)
        max_bid = min([max_bid, MAXIMUM_BID])
        position_budget = random.randint(1, max_bid)
        budget_remaining -= position_budget
        pp_draft_budget.append({'position': position, 'budget': position_budget, 'drafted': False})

    if budget_remaining > 0:
        distribute(budget_remaining, pp_draft_budget)
    return sorted(pp_draft_budget, key=lambda p: p['budget'], reverse=True)


def draft(draft_budgets):
    draft_data = read_data()
    pick = 0
    drafted_positions = {p: 0 for p in list(ROSTER_SIZE.keys())}
    draft_results = [[] for _ in range(NUM_TEAMS)]

    # XXX could this just be one long array of positions?
    pps_remaining_by_team = [[] for _ in range(NUM_TEAMS)]
    for team in range(len(pps_remaining_by_team)):
        for position, count in ROSTER_SIZE.items():
            pps_remaining_by_team[team].extend([position for _ in range(count)])
        random.shuffle(pps_remaining_by_team[team])

    for round_pick in range(sum(ROSTER_SIZE.values())):
        for team in range(len(pps_remaining_by_team)):
            position = pps_remaining_by_team[team][round_pick]
            player = draft_data[position][drafted_positions[position]]
            player['pick'] = pick
            player['position'] = position
            log(DEBUG, 'Pick {}: Team {} nominates {} {}'.format(pick, team, position, player['Player Name']))

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

            player_copy = copy.copy(player)
            player_copy['value'] = winning_bid['budget']
            winning_bid['drafted'] = True
            draft_results[winning_team].append(player_copy)

            drafted_positions[position] += 1
            pick += 1
            log(DEBUG, 'Pick {}: Team {} drafts {} {} for ${}'.format(pick, winning_team, position, player['Player Name'], winning_bid['budget']))

    return draft_results


def sanity_check(draft_budget):
    budget = sum([p['budget'] for p in draft_budget])
    if budget != AUCTION_BUDGET:
        print('OVER BUDGET!!! ({})'.format(budget))
        pprint.pprint(draft_budget)


def make_draft_budget_key(draft_budget):
    sanity_check(draft_budget) # XXX
    return '-'.join(['{}:{}'.format(player['position'], player['budget'])
                    for player in draft_budget])


def draft_budget_key_to_budgets(budget_key):
    draft_budgets = []
    position_budgets = budget_key.split('-')
    for position_budget in position_budgets:
        p, b = position_budget.split(':')
        draft_budgets.append({'position': p, 'budget': int(b), 'drafted': False})
    sanity_check(draft_budgets) # XXX
    return draft_budgets


def record_draft_results(current_generation, drafts_results):
    log(DETAIL, 'Generation', current_generation, 'Results')
    player_values = player_value_above_replacement()
    for draft_results in drafts_results:
        for team in range(len(draft_results)):
            draft_result = draft_results[team]
            score = sum([player_values[player['Player Name']] for player in draft_result])

            draft_budget = [{'position': player['position'], 'budget': player['value'], 'Player Name': player['Player Name']} for player in draft_result]
            draft_budget.sort(key=lambda p: (p['budget'],p['position']), reverse=True)

            budget_key = make_draft_budget_key(draft_budget)
            DRAFT_BUDGETS_AGE[budget_key]['age'] += 1
            DRAFT_BUDGETS_AGE[budget_key]['total'] += score

            log(DETAIL, 'Team', team, 'draft score:', score)
            log(DETAIL, '\n'.join(['{}: {} {}'.format(b['position'], b['budget'], b['Player Name']) for b in draft_budget]))
            log(DETAIL, '')
    log(DETAIL, 'Completed generation', current_generation)
    log(DETAIL, '')


def spawn_next_generation(drafts_results):
    # select the top fit team drafts
    fit_budgets = []
    combined_results = []
    for draft_results in drafts_results:
        for draft_result in draft_results:
            draft_budget = [{'position': player['position'], 'budget': player['value'], 'Player Name': player['Player Name'], 'fpts': player['fpts']} for player in draft_result]
            draft_budget.sort(key=lambda p: (p['budget'], p['position']), reverse=True)
            combined_results.append(draft_budget)
    #combined_results.sort(key=lambda d: sum([float(player['fpts']) for player in d]), reverse=True)
    combined_results.sort(
        key=lambda d: DRAFT_BUDGETS_AGE[make_draft_budget_key(d)]['total'] / DRAFT_BUDGETS_AGE[make_draft_budget_key(d)]['age'],
        reverse=True)

    for draft_number in range(FITNESS):
        budget_key = make_draft_budget_key(combined_results[draft_number])
        fit_budgets.append(budget_key)
        for player in combined_results[draft_number]:
            if DRAFT_BUDGETS_AGE[budget_key]['age'] > 5:
                PLAYER_BUDGETS[player['position']][player['Player Name']].append(player['budget'])

        # mutate team drafts
        # if random.random() < 0.10:
        #     i = random.randint(0, len(fit_budgets)-2)
        #     fit_budgets[i+1], fit_budgets[i] = fit_budgets[i], fit_budgets[i+1]
        #     fit_budgets_by_team[team].append(fit_budgets)

    # make hybrid team drafts from fit parents

    # pair up top team drafts to make full draft for next generation
    next_gen_draft_budgets = []
    # XXX not sure what to call this magic number... matings?
    for _ in range(int(POPULATION_SIZE * 0.75)):
        draft_budgets = []
        for team in range(NUM_TEAMS):

            draft_budgets.append(draft_budget_key_to_budgets(random.choice(fit_budgets)))
        next_gen_draft_budgets.append(draft_budgets)

    return next_gen_draft_budgets


def median(lst):
    lst = sorted(lst)
    if len(lst) < 1:
            return None
    if len(lst) %2 == 1:
            return lst[int((len(lst)+1)/2)-1]
    else:
            return int((float(sum(lst[int(len(lst)/2)-1:int(len(lst)/2)+1]))/2.0) + 0.5)


def main():
    player_values = player_value_above_replacement()
    generation_draft_budgets = []
    for generation in range(GENERATIONS):
        for _ in range(POPULATION_SIZE - len(generation_draft_budgets)):
            draft_budgets = []
            for team in range(NUM_TEAMS):
                team_budget = get_random_pp_draft_budget()
                log(DEBUG, 'Team', team, 'budgets', make_draft_budget_key(team_budget))
                draft_budgets.append(team_budget)
            generation_draft_budgets.append(draft_budgets)

        draft_results = []

        pool = Pool()
        draft_results = pool.map(draft, generation_draft_budgets)
        pool.close()
        pool.join()

        record_draft_results(generation, draft_results)
        generation_draft_budgets = spawn_next_generation(draft_results)

        for position in sorted(PLAYER_BUDGETS.keys()):
            log(INFO, '{} player values:'.format(position))
            log(INFO, ','.join(['player', 'position', 'points_above_replacement', 'min_auction_value', 'median_auction_value', 'max_auction_value']))
            for player in sorted(PLAYER_BUDGETS[position], key=lambda p: median(PLAYER_BUDGETS[position][p]), reverse=True):
                med = median(PLAYER_BUDGETS[position][player])
                log(INFO, ','.join([str(s) for s in [player,
                              position,
                              player_values[player],
                              min(PLAYER_BUDGETS[position][player]),
                              med,
                              max(PLAYER_BUDGETS[position][player])]]))
            log(INFO, '')

        log(STANDARD, 'Generation {} summary of drafting budgets:'.format(generation))
        sorted_budgets_by_age = sorted([d for d in list(DRAFT_BUDGETS_AGE.items()) if d[1]['age'] >= min(generation, 5)],
                                       key=lambda d: d[1]['total'] / d[1]['age'],
                                       reverse=True)

        for i in range(10):
            if i >= len(sorted_budgets_by_age):
                break
            budgets, budgets_age = sorted_budgets_by_age[i]
            log(STANDARD, ' ', int(budgets_age['age']),
                _round(budgets_age['total'] / budgets_age['age']), '(' + budgets + ')')
        log(STANDARD, '')


if __name__ == '__main__':
    main()
