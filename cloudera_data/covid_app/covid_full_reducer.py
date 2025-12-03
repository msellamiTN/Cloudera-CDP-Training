#!/usr/bin/env python

import sys

current_country = None
current_confirmed = 0
current_recovered = 0.0
current_deaths = 0

# Input comes from STDIN (standard input)
for line in sys.stdin:
    # Remove leading and trailing whitespace
    line = line.strip()
    
    # Parse the input we got from mapper.py (tab-delimited)
    country, values = line.split('\t')
    
    # Parse the values part (comma-delimited)
    province, date, confirmed, recovered, deaths = values.split(',')
    
    # Convert data types
    confirmed = int(confirmed)
    recovered = float(recovered)
    deaths = int(deaths)
    
    # If we switch to a new country, output the sum for the last country
    if current_country and current_country != country:
        print(f"{current_country}\t{current_confirmed},{current_recovered},{current_deaths}")
        current_confirmed = 0
        current_recovered = 0.0
        current_deaths = 0
    
    current_country = country
    current_confirmed += confirmed
    current_recovered += recovered
    current_deaths += deaths

# Output the last country if needed
if current_country:
    print(f"{current_country}\t{current_confirmed},{current_recovered},{current_deaths}")
