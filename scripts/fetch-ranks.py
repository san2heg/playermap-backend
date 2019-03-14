# Script to scrape seasonal player rankings from basketball-reference.com
# Uses scraped data in combination with monthly player team-location data to
# create monthly lists of players and their teams during that month. Script
# includes option to update mongoDB database with monthly records.

# Example usage:
# python fetch-ranks --year=1998 --month=9
#   => outputs top ranked players of September, 1998 with their respective teams
# python fetch-ranks --all
#   => outputs top ranked players for each month from the beginning of the NBA
#      to current day
# python fetch-ranks --all --update
#   => also updates mongoDB database with newly fetched records

import urllib2
from bs4 import BeautifulSoup
import sys
import argparse

def get_rankings_url(year):
    return 'https://www.basketball-reference.com/leagues/NBA_' + str(2019) + '_advanced.html'

def main():
    # Get command line arguments
    parser=argparse.ArgumentParser()
    parser.add_argument('--month', '-m', help='Specify month (1-12)', type=int)
    parser.add_argument('--year', '-y', help='Specify year', type=int)
    parser.add_argument('--all', help='Fetch for every month until present day', action='store_true')
    parser.add_argument('--update', '-u', help='Update database entries', action='store_true')

    args = parser.parse_args()

    if not args.all and (args.month == None or args.year == None):
        sys.exit('Specify value for month and year')

if __name__ == '__main__':
    main()
