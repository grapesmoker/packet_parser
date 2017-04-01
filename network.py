#!/usr/bin/env python
import requests
import sys
import os
from bs4 import BeautifulSoup

t_base = 'http://www.hsquizbowl.org/db/'
base = t_base + 'questionsets/search'
dest = 'archive'


def fetch_packets(url, path):

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    title = soup.find(class_='First').find('h2').text
    tournament_path = os.path.join(path, title)
    if not os.path.exists(tournament_path):
        os.mkdir(tournament_path)

    print('fetching packets for {}'.format(title))
    packet_urls = [link.get('href') for link in soup.find('ul', class_='FileList').find_all('a')]

    for packet_url in packet_urls:
        filename = packet_url.split('/')[-1]
        packet_path = os.path.join(tournament_path, title + ' - ' + filename)
        r = requests.get(packet_url, stream=True)
        with open(packet_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)


def get_season_tournaments(year):

    year_path = os.path.join(os.path.abspath('.'), dest, str(year))
    if not os.path.exists(year_path):
        os.mkdir(year_path)

    params = {'col': 1, 'open': 1, 'season': year, 'archived': 'y'}

    r = requests.get(base, params=params)

    soup = BeautifulSoup(r.text, 'lxml')

    tournaments = soup.find_all(class_='Name')
    page_selector = soup.find('PageSelector')
    if page_selector:
        pages = len(page_selector.find_all('a'))
    else:
        pages = 1

    for i in range(pages - 1):
        r = requests.get(base + '{}/'.format(pages), params=params)
        soup = BeautifulSoup(r.text, 'lxml')
        tournaments.extend(soup.find_all(class_='Name'))

    tournament_links = [t_base + t.find('a').get('href') for t in tournaments]

    for url in tournament_links:
        fetch_packets(url, year_path)

if __name__ == '__main__':

    year = sys.argv[1]

    get_season_tournaments(year)