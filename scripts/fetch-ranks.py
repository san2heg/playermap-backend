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
import datetime
import pymongo
import shutil
import bson
from bson.binary import Binary
import dns
from bs4 import BeautifulSoup
import sys
import argparse
import base64
import time
import requests
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join('.', '.env'))

MSF_USER = os.getenv('MSF_USER')
MSF_PASS = os.getenv('MSF_PASS')
DB_PASS = os.getenv('DB_PASS')

NBA_START = 1974

HEADSHOTS_DIR = '../headshots/'

def rankings_url(year):
    return 'https://www.basketball-reference.com/leagues/NBA_' + str(year) + '_advanced.html'

# Return list of players and their rankings given some year
def scrape_rankings(year, limit):
    print('> Scraping top ' + str(limit) + ' for ' + str(year) + ' <')

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
        name_list = p.split(' ')
        firstname = name_list[0]
        lastname = ' '.join(name_list[1:])
        players_dict[p] = {'rank': r+1, 'team': t, 'br_pid': pid, 'firstname': firstname, 'lastname': lastname}

    return players_dict

# Fetch png headshot for some player, saved in tmp directory
def fetch_headshot(firstname, lastname, br_pid):
    print('> Fetching headshot for ' + firstname + ' ' + lastname + ' <')
    r = requests.get('https://d2cwpp38twqe55.cloudfront.net/req/201902151/images/players/'+br_pid+'.jpg', stream=True, allow_redirects=False)
    if r.status_code == 302:
        print('\tHeadshot not found')
        return False
    elif r.status_code != 200:
        print('\tError fetching headshot: ' + str(r.status_code))
        return False
    filename = br_pid + '.jpg'
    dirpath = os.path.join(HEADSHOTS_DIR, filename)
    with open(dirpath, 'w+') as f:
        f.write(r.content)
    return True

# Format output
def pretty_print(rankings):
    res_list = []
    for k,v in rankings.iteritems():
        res_list.append((v['rank'], v['team'], k))
    res_list.sort()

    for r, t, fn in res_list:
        print(str(r) + ': ' + str(fn) + ' - ' + str(t))

# Overlap report
def overlap_report(year1, year2):
    playerobj1 = year1['players']
    playerobj2 = year2['players']

    overlap = []
    for k in playerobj1:
        if k in playerobj2:
            overlap.append(k)

    return overlap

def main():
    # Get command line arguments
    parser=argparse.ArgumentParser()
    parser.add_argument('--year', '-y', help='Specify year', type=int)
    parser.add_argument('--all', help='Fetch for every year until present day', action='store_true')
    parser.add_argument('--update', '-u', help='Update database entries', action='store_true')
    parser.add_argument('--limit', '-l', help='Define top LIMIT players to output', type=int, default=50)
    parser.add_argument('--pretty', '-p', help='Pretty print output', action='store_true')
    parser.add_argument('--img', '-i', help='Fetch and upload headshots', action='store_true')
    parser.add_argument('--throttle', '-t', help='Throttle scraping requests to prevent overload', action='store_true')
    parser.add_argument('--replace', '-r', help='Replace existing headshots with new ones. Requires --img', action='store_true')

    args = parser.parse_args()

    if not args.all and args.year == None:
        sys.exit('Specify value for year')
    if args.replace and not args.img:
        sys.exit('--replace option requires --img')

    # Initialize DB connection if necessary
    if args.update:
        print('> Connecting to DB <')
        client = pymongo.MongoClient('mongodb+srv://san2heg:'+DB_PASS+'@nba-trade-map-aoy8h.mongodb.net/test?retryWrites=true')
        db = client['players']
        rankings_col = db['rankings']

    def fetch(year):
        res = scrape_rankings(year, args.limit)
        if args.pretty:
            pretty_print(res)
        else:
            print(res)
        if args.update:
            # Update database
            r_update = rankings_col.update_one({'year': year}, {'$set': {'players': res}}, upsert=True)
            print('> DB players.rankings updated. Matched: ' + str(r_update.matched_count) + ', Modified: ' + str(r_update.modified_count) + '. Entry possibly inserted <')
            if args.img:
                # Fetch headshot if necessary and save to filesystem
                for p,obj in res.iteritems():
                    filename = obj['br_pid'] + '.jpg'
                    headshot_exists = os.path.isfile(os.path.join(HEADSHOTS_DIR, filename))

                    if not args.replace and headshot_exists:
                        print('> Headshot for '+ p + ' already exists in filesystem, continuing... <')
                        continue

                    if args.throttle:
                        time.sleep(0.5)
                    if fetch_headshot(obj['firstname'], obj['lastname'], obj['br_pid']):
                        print('\tHeadshot saved to filesystem')

    if not args.all:
        fetch(args.year)
    else:
        curr_year = int(datetime.datetime.now().year)
        for y in range(NBA_START, curr_year+1):
            fetch(y)

if __name__ == '__main__':
    main()
