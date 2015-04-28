#!/usr/bin/env python
# requires wv on linux
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

def send_json_data(json_file, url):

    data = json.load(open(json_file, 'r'))

    #print url
    #r = requests.get(url)
    #print r.text

    tournament = data['tournament']
    year = data['year']

    print year, tournament
    
    #headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, json=data) #, headers=headers)

    with open('err.html', 'w') as f:
        f.write(r.content)
        
        



def parser_driver(doc_file, mode='json'):

    p = Packet('test')
    p.load_packet_from_file(doc_file)
    p.is_valid()
    
def parse_packets(filenames, mode='json'):

    for doc_file in filenames:
        tossups, bonuses = parse_packet(docfile)

def parse_directory(dirname, mode='json'):

    tour = Tournament()
    tour.create_tournament_from_directory(dirname)

    tour_json_file = os.path.join(dirname, '{0} {1}.json'.format(tour.year, tour.tour_name))
    
    if mode == 'json':
        if tour.is_valid():
            json.dump(tour.to_dict(), open(tour_json_file, 'w'), indent=4)
    
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest='file')
    parser.add_argument('-d', '--dir', dest='dir')
    parser.add_argument('-o', '--operation', dest='operation')
    parser.add_argument('-s', '--spec', dest='spec')
    parser.add_argument('-m', '--mode', dest='mode', default='json')
    parser.add_argument('-u', '--url', dest='url')
    parser.add_argument('-op', '--output-file', dest='output_file')
    
    args = parser.parse_args()

    if args.dir is not None and args.operation == 'process':
        #os.path.walk(args.dir, process_dir_super(not args.spec == 'html'), None)
        parse_directory(args.dir, args.mode)
 

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
