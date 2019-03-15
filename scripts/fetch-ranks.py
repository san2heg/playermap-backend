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

import os
import urllib2
from bs4 import BeautifulSoup
import sys
import argparse
import base64
import requests
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join('.', '.env'))

MSF_USER = os.getenv('MSF_USER')
MSF_PASS = os.getenv('MSF_PASS')

def rankings_url(year):
    return 'https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_advanced.html'

# Return list of players and their rankings given some year
def scrape_rankings(year, limit):
    print('Scraping top ' + str(limit) + ' for ' + str(year))

    page = urllib2.urlopen(rankings_url(year))
    soup = BeautifulSoup(page, 'html.parser')

    players = []
    table = soup.find(id='all_advanced_stats').tbody
    for row in table.find_all('tr', {'class': 'full_table'}):
        vorp = float(row.find('td', {'data-stat': 'vorp'}).string)
        player = row.find('td', {'data-stat': 'player'}).find('a').string
        player_id = row.find('td', {'data-stat': 'player'})['data-append-csv']
        team = row.find('td', {'data-stat': 'team_id'}).string
        players.append((player_id, player, vorp, team))

    players.sort(key=lambda t: t[2], reverse=True)
    players = players[:limit]

    players_dict = {}
    for r,(pid,p,_,t) in enumerate(players):
        players_dict[pid] = {'rank': r+1, 'team': t, 'fullname': p}

    return players_dict

def main():
    # Get command line arguments
    parser=argparse.ArgumentParser()
    parser.add_argument('--year', '-y', help='Specify year', type=int)
    parser.add_argument('--all', help='Fetch for every year until present day', action='store_true')
    parser.add_argument('--update', '-u', help='Update database entries', action='store_true')
    parser.add_argument('--limit', '-l', help='Define top LIMIT players to output', type=int, default=50)
    parser.add_argument('--pretty', '-p', help='Pretty print output', action='store_true')

    args = parser.parse_args()

    if not args.all and args.year == None:
        sys.exit('Specify value for year')

    if not args.pretty:
        print(scrape_rankings(args.year, args.limit))
    else:
        # Formatting
        res = scrape_rankings(args.year, args.limit)
        res_list = []
        for k,v in res.iteritems():
            res_list.append((v['rank'], v['team'], v['fullname']))
        res_list.sort()

        for r, t, fn in res_list:
            print(str(r) + ': ' + str(fn) + ' - ' + str(t))

if __name__ == '__main__':
    main()
