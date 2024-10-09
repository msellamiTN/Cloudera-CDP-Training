#!/usr/bin/env python

import sys
import csv

# Input comes from STDIN (standard input)
for line in sys.stdin:
    # Remove leading and trailing whitespace
    line = line.strip()
    
    # Use csv reader to parse the input line (ignoring any headers)
    reader = csv.reader([line])
    for row in reader:
        # Skip header or any line that doesn't have the expected number of columns
        if len(row) < 8 or row[0] == 'Unnamed: 0':
            continue
        
        # Extract the fields
        province = row[1]
        country = row[2]
        lat = row[3]
        long = row[4]
        date = row[5]
        confirmed = int(row[6])
        recovered = float(row[7]) if row[7] else 0.0
        deaths = int(row[8])
        
        # Output key-value pair: Country as key, and the relevant data as value
        print(f"{country}\t{province},{date},{confirmed},{recovered},{deaths}")
