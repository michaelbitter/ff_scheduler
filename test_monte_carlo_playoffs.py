#!/usr/bin/env python

import monte_carlo_playoffs

records = [{
    'Aces': 5,
    'Burns': 7,
    'Cheatin': 7,
    'Grizwalds': 5,
    'Halloween': 9,
    'Jokers': 3,
    'Jongs': 7,
    'Studs': 7,
    'Torture': 6,
    'Woodhead': 9,
}]

monte_carlo_playoffs.evaluate_records(records)
