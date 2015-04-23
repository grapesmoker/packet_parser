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

from pprint import pprint

from pprint import pprint

from Tossup import Tossup
from Bonus import Bonus
from utils import ansregex, bpart_regex, is_answer, is_bpart, get_bonus_part_value, sanitize


class InvalidPacket(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 80 + '\n'
        s += 'There was a problem in packet {0}\n'.format(self.args[0])
        s += '*' * 80 + '\n'

        return s

def convert_doc_to_html(doc_file):

    doc_file = os.path.abspath(doc_file)

    print doc_file
    
    if re.search('docx', doc_file):
        html_file = re.sub('docx', 'html', doc_file)
    elif re.search('doc', doc_file):
        html_file = re.sub('doc', 'html', doc_file)
    else:
        print "not valid input format"

    print html_file
        
    cmd = 'pandoc -f docx -t html -o "{0}" "{1}"'.format(html_file, doc_file)
    print cmd
    cmd = shlex.split(cmd)
    
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    
    return html_file

def prepare_html_file(html_file, skip_lines=2):
    
    with codecs.open(html_file, 'r', encoding='utf-8') as f:
        packet_contents = f.read()
        
    packet_contents = map(lambda x: sanitize(x, valid_tags=['em', 'strong']), packet_contents.split('\n'))
    packet_contents = [x.strip() for x in packet_contents if x.strip() != '' and len(x) > 20]
    
    return packet_contents[skip_lines:]
        

def parse_packet(packet_contents):
    
    parser_stack = []
    
    tossups = []
    bonuses = []
    
    for i, item in enumerate(packet_contents):
        
        if not is_answer(item) and not is_bpart(item) and not len(parser_stack) < 2:
            # pop the stack
            result = []
            while parser_stack != []:
                result.append(parser_stack.pop())
            result.reverse()
        
            if len(result) == 2 and is_answer(result[1]) and not is_answer(result[0]) and not is_bpart(result[0]):
                answer = re.sub(ansregex, '', result[1])
                question = result[0]
                new_tossup = Tossup(question=question, answer=answer)
                tossups.append(new_tossup)
                    
            if len(result) > 2 and (len(result) % 2 == 1) and is_answer(result[-1]) and not is_answer(result[0]):
                bonus_parts = result[1::2]
                answers = map(lambda x: re.sub(ansregex, '', x), result[2::2])
                leadin = result[0]
                bonus = Bonus(leadin=leadin, parts=bonus_parts, answers=answers)
                bonuses.append(bonus)
                
            parser_stack.append(item)
        else:
            parser_stack.append(item)
                
    return tossups, bonuses

def parser_driver(doc_file, mode='json'):

    html_file = convert_doc_to_html(doc_file)
    packet_contents = prepare_html_file(html_file)

    tossups, bonuses = parse_packet(packet_contents)

    for tu in tossups:
        print unicode(tu)

def parse_packets(filenames, mode='json'):

    for doc_file in filenames:
        tossups, bonuses = parse_packet(docfile)
        
        
    
if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest='file')
    parser.add_argument('-d', '--dir', dest='dir')
    parser.add_argument('-o', '--operation', dest='operation')
    parser.add_argument('-s', '--spec', dest='spec')
    parser.add_argument('-m', '--mode', dest='mode', default='json')
    parser.add_argument('-op', '--output-file', dest='output_file')
    
    args = parser.parse_args()

    if args.dir is not None and args.operation == 'process':
        os.path.walk(args.dir, process_dir_super(not args.spec == 'html'), None)

    if args.file is not None and args.operation is not None:
        if args.operation == 'process':
            parser_driver(args.file)

        if args.operation == 'validate':
            validate_json(args.file)

        if args.operation == 'import':
            import_json_into_mongo(args.file)

    if args.operation == 'conf' and args.dir is not None and args.spec is not None:
        conf_gen(args.dir, args.spec)
