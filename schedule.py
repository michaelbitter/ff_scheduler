#!/usr/bin/env python

import sys

div1_teams = ['Patrick', 'Chris', 'David', 'Jaden', 'Michael']
div2_teams = ['Scott', 'DaveW', 'Mike', 'DaveM', 'Dallas']
week_ordering = [2, 1, 3, 9, 10, 11, 12, 8, 4, 5, 6, 7, 13]

order = 1
for week in sorted(week_ordering):
    try:
        assert order == week
    except AssertionError:
        print "Error: Got Week {} but expected Week {}, it looks like week_ordering is missing/contains duplicate weeks.".format(week, order)
        sys.exit(1)
    order += 1

teams = div1_teams + div2_teams
div2_teams.reverse()

def matchup(teams):
    num_teams = len(teams)+1
    static = teams.pop(0)
    matchups = [[static, teams[0]]]
    for i in range(1, num_teams/2):
        matchups.extend([[teams[i], teams[-i]]])

    teams.insert(0, static)
    return matchups
    
def print_matchups(week, matchups):
    print "Week", week, "schedule:"
    for teams in matchups:
        print "\t", teams[0], "vs", teams[1]
    print

def find_additional_matchup(team, matchups):
    for matchup in matchups:
        if matchup[0] == team:
            return matchup
    raise Exception('Team {} not found in matchups {}'.format(
        team, matchups))

def warn_on_duplicates(prev, curr):
    for curr_teams in curr:
        for prev_teams in prev:
            if sorted(curr_teams) == sorted(prev_teams):
                print "Warning: Duplicate matchup between {} and {}".format(curr_teams[0], curr_teams[1])

season_matchups = []
# Week 1 - 8
for week in range(1, 9):
    matchups = matchup(teams)
    season_matchups.append(matchups)
    #print_matchups(week, matchups)
    teams = teams + [teams.pop(1)]

# Week 9 - 12
# Week 9 would have been one league vs the other
# Make 4 more matchups where each team plays the team
# in the same division one more time. The bonus
# matchup is one taken from what would have been week 9.
additional_matchups = matchup(teams)
for week in range(9, 13):
    odd_man1 = div1_teams.pop()
    odd_man2 = div2_teams.pop()
    additional_matchup = find_additional_matchup(odd_man1, additional_matchups)
    
    div1_matchups = matchup(div1_teams)
    div2_matchups = matchup(div2_teams)
    season_matchups.append(div1_matchups + div2_matchups + [additional_matchup])
    #print_matchups(week, div1_matchups + div2_matchups + [additional_matchup])
    div1_teams.append(odd_man1)
    div2_teams.append(odd_man2)
    div1_teams = div1_teams + [div1_teams.pop(1)]
    div2_teams = div2_teams + [div2_teams.pop(1)]

# Week 13
# The static teams (one per division) from weeks
# 9-12 needs to use their matchup from the split
# up week 9.
odd_man1 = div1_teams.pop(0)
odd_man2 = div2_teams.pop(0)
additional_matchup = find_additional_matchup(odd_man1, additional_matchups)
div1_teams = div1_teams + [div1_teams.pop(1)]
div2_teams = div2_teams + [div2_teams.pop(1)]
div1_matchups = matchup(div1_teams)
div2_matchups = matchup(div2_teams)
season_matchups.append(div1_matchups + div2_matchups + [additional_matchup])
#print_matchups(13, div1_matchups + div2_matchups + [additional_matchup])

week = 1
previous_matchups = None
for order in week_ordering:
    current_matchups = season_matchups[order-1]
    print_matchups(week, current_matchups)
    if previous_matchups:
        warn_on_duplicates(previous_matchups, current_matchups)
    previous_matchups = current_matchups
    week += 1
