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

rankings_cache = {}

def rankings_url(year):
    return 'https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_advanced.html'

# Return list of players and their rankings given some year
def scrape_rankings(year, limit):
    if rankings_cache.get((year, limit)) != None:
        return rankings_cache[(year, limit)]

    page = urllib2.urlopen(rankings_url(year))
    soup = BeautifulSoup(page, 'html.parser')

    players = []
    table = soup.find(id='all_advanced_stats').tbody
    for row in table.find_all('tr', {'class': 'full_table'}):
        vorp = float(row.find('td', {'data-stat': 'vorp'}).string)
        player = row.find('td', {'data-stat': 'player'}).string
        players.append((player, vorp))

    players.sort(key=lambda t: t[1], reverse=True)

    rankings_cache[(year, limit)] = players[:limit]
    return rankings_cache[(year, limit)]

# Return dictionary of players and their teams given some month and year
def fetch_player_teams(month, year):
    # Make request to MySportsFeeds
    try:
        response = requests.get(
            url='https://api.mysportsfeeds.com/v1.2/pull/nba/'+str(year-1)+'-'+str(year)+'-regular/roster_players.json',
            params={
                "fordate": str(year) + str(month) + '15'
            },
            headers={
                "Authorization": "Basic " + base64.b64encode('{}:{}'.format(MSF_USER, MSF_PASS).encode('utf-8')).decode('ascii')
            }
        )
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

    player_list = response.json()['rosterplayers']['playerentry']

    players = {}
    for p in player_list:
        if 'team' in p:
            players[p['player']['FirstName'] + ' ' + p['player']['LastName']] = p['team']['Abbreviation']

    return players

# Return dictionary of top X players given some month and year, associating
# players with their team at that time
def ranked_players(month, year, X):
    season_ranks = scrape_rankings(year, X)
    player_teams = fetch_player_teams(month, year)

    table = {}
    for rank,(player,_) in enumerate(season_ranks):
        table[player] = {'rank': rank+1, 'team': player_teams[player] if player_teams.get(player) != None else 'NOT FOUND'}

    return table

def main():
    # Get command line arguments
    parser=argparse.ArgumentParser()
    parser.add_argument('--month', '-m', help='Specify month (1-12)', type=int)
    parser.add_argument('--year', '-y', help='Specify year', type=int)
    parser.add_argument('--all', help='Fetch for every month until present day', action='store_true')
    parser.add_argument('--update', '-u', help='Update database entries', action='store_true')
    parser.add_argument('--limit', '-l', help='Define top LIMIT players to output', type=int, default=50)
    parser.add_argument('--pretty', '-p', help='Pretty print output', action='store_true')

    args = parser.parse_args()

    if not args.all and (args.month == None or args.year == None):
        sys.exit('Specify value for month and year')

    # print(fetch_player_teams(args.month, args.year))
    # print(scrape_rankings(args.year, args.limit))

    if not args.pretty:
        print(ranked_players(args.month, args.year, args.limit))
    else:
        # Formatting
        res = ranked_players(args.month, args.year, args.limit)
        res_list = []
        for k,v in res.iteritems():
            res_list.append((v['rank'], k, v['team']))
        res_list.sort()

        for r, p, t in res_list:
            print(str(r) + ': ' + str(p) + ' - ' + str(t))

if __name__ == '__main__':
    main()
