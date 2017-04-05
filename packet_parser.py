#!/usr/bin/env python3

import os
import sys
import re
import shlex
import subprocess
import string

import os.path
import glob
import json
import argparse
import codecs
import requests

from pprint import pprint

from pprint import pprint

from Tossup import Tossup
from Bonus import Bonus
from Packet import Packet
from Tournament import Tournament

from utils import conf_gen
from network import get_season_tournaments


def send_json_data(json_file, url):

    data = json.load(open(json_file, 'r'))

    tournament = data['tournament']
    year = data['year']

    print(year, tournament)
    
    r = requests.post(url, json=data)

    with open('err.html', 'w') as f:
        f.write(r.content)


def parser_driver(doc_file, mode='json'):

    p = Packet('test')
    p.load_packet_from_file(doc_file)
    p.is_valid()


def parse_packets(filenames, mode='json'):

    for doc_file in filenames:
        tossups, bonuses = parse_packet(docfile)


def parse_directory(dirname, mode='json', reuse_html=False):

    tour = Tournament()
    tour.create_tournament_from_directory(dirname, reuse_html=reuse_html)

    tour_json_file = os.path.join(dirname, '{0} {1}.json'.format(tour.year, tour.tour_name))
    
    if mode == 'json':
        if tour.is_valid():
            json.dump(tour.to_dict(), open(tour_json_file, 'w'), indent=4)
    
if __name__ == '__main__':
    #reload(sys)
    #sys.setdefaultencoding('utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest='file')
    parser.add_argument('-d', '--dir', dest='dir')
    parser.add_argument('-o', '--operation', dest='operation')
    parser.add_argument('-s', '--spec', dest='spec')
    parser.add_argument('-m', '--mode', dest='mode', default='json')
    parser.add_argument('-u', '--url', dest='url')
    parser.add_argument('-y', '--year', dest='year', type=int)
    parser.add_argument('--reuse-html', type=bool, default=False)
    parser.add_argument('-op', '--output-file', dest='output_file')
    
    args = parser.parse_args()

    if args.dir is not None and args.operation == 'process':
        parse_directory(args.dir, args.mode, args.reuse_html)

    if args.file is not None and args.operation == 'test':
        packet = Packet('test')
        packet.load_packet_from_file(args.file, test=True)

    if args.file is not None and args.operation is not None:
        if args.operation == 'process':
            parser_driver(args.file)

        if args.operation == 'validate':
            validate_json(args.file)

        if args.operation == 'import':
            import_json_into_mongo(args.file)

    if args.operation == 'conf' and args.dir is not None and args.spec is not None:
        conf_gen(args.dir, args.spec)

    if args.operation == 'send' and args.url is not None and args.file is not None:
        send_json_data(args.file, args.url)

    if args.operation == 'fetch' and args.year:
        get_season_tournaments(args.year)