#!/usr/bin/env python

import pprint

from collections import defaultdict

TEAMS = {
    'Torture': 6,
    'Aces': 5,
    'Halloween': 8,
    'Woodhead': 9,
    'Cheatin': 7,
    'Jongs': 6,
    'Studs': 6,
    'Grizwalds': 5,
    'Burns': 6,
    'Jokers': 2,
}

MATCHUPS = [[
#     ('Torture', 'Cheatin'),
#     ('Jokers', 'Aces'),
#     ('Halloween', 'Grizwalds'),
#     ('Woodhead', 'Burns'),
#     ('Jongs', 'Studs'),
# ], [
    ('Torture', 'Jongs'),
    ('Cheatin', 'Studs'),
    ('Halloween', 'Grizwalds'),
    ('Burns', 'Aces'),
    ('Jokers', 'Woodhead'),
]]

NUM_PLAYOFF_TEAMS = 6
    
def get_winners(week, i):
    winners = []
    for matchup in week:
        if i % 2 == 0:
            winners.append(matchup[0])
        else:
            winners.append(matchup[1])
        i = i / 2
    return winners

def evaluate_records(records):
    attempts = len(records) + 0.0
    successes = {
        'POINTS': defaultdict(int),
        'WINS': defaultdict(int),
    }
    for record in records:
        standings = sorted(record.iteritems(), key=lambda (k,v): (v,k), reverse=True)
        playoff_teams = 0
        current_wins = standings[0][1]
        current_win_index = 0
        for i in range(len(standings)):
            if playoff_teams >= NUM_PLAYOFF_TEAMS:
                break
            if standings[i][1] != current_wins:
                #record winners
                reason = 'WINS'
                playoff_teams += len(standings[current_win_index:i])
                if playoff_teams > NUM_PLAYOFF_TEAMS:
                    reason = 'POINTS'
                for teams in standings[current_win_index:i]:
                    successes[reason][teams[0]] += 1
                #update current
                current_wins = standings[i][1]
                current_win_index = i

    totals = defaultdict(int)
    for reason, teams in successes.iteritems():
        print "{}:".format(reason)
        for team, wins in teams.iteritems():
            print "{} {:.1f}%".format(team, wins * 100.0 / attempts)
            totals[team] += wins
        print
    print "TOTAL:"
    for team, wins in totals.iteritems():
        print "{} {:.1f}%".format(team, wins * 100.0 / attempts)
    pprint.pprint(records)
    pprint.pprint(successes)
        
def main():
    monte_carlo_tree = {}
    mc_records = [TEAMS]
    week_num = 1
    for week in MATCHUPS:
        next_mc_records = []
        for mc_record in mc_records:
            for i in range(2**len(week)):
                winners = get_winners(week, i)
                new_standings = mc_record.copy()
                skip = False
                for winner in winners:
                    new_standings[winner] += 1
                    if winner in ('') and week_num == 1:
                        skip = True
                if not skip:
                    next_mc_records.append(new_standings)
        mc_records = next_mc_records
        week_num += 1

    evaluate_records(mc_records)

if __name__ == '__main__':
    main()
