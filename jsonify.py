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

# import pymongo

from pprint import pprint
# from pymongo import MongoClient

try:
    conn = MongoClient('localhost', 27017)
    db = conn.qbdb
    tournaments = db.tournaments
    packets = db.packets
    tossups = db.tossups
    bonuses = db.bonuses

except Exception as ex:
    print 'Mongo not available'

# import lxml.html as HTML

from bs4 import BeautifulSoup, Comment
from pprint import pprint

latex_preamble = r'''
\documentclass[10pt]{article}
\usepackage[top=1in, bottom=1in, left=1in, right=1in]{geometry}
\usepackage{parskip}
\usepackage[]{graphicx}
\usepackage[normalem]{ulem}
\usepackage{ebgaramond}
\usepackage[utf8]{inputenc}

\begin{document}

\newcommand{\ans}[1]{{\sc \uline{#1}}}

\newcommand{\tossups}{\newcounter{TossupCounter} \noindent {\sc Tossups}\\}
\newcommand{\tossup}[2]{\stepcounter{TossupCounter}
    \arabic{TossupCounter}.~#1\\ANSWER: #2\\}

\newcommand{\bonuses}{\newcounter{BonusCounter} \noindent {\sc Bonuses} \\}
% bonus part is points - text - answer
\newcommand{\bonuspart}[3]{[#1]~#2\\ANSWER: #3\\}
% bonus is leadin - parts

\newenvironment{bonus}[1]{\stepcounter{BonusCounter}
    \arabic{BonusCounter}.~#1\\}{}


%\newcommand{\bonus}[2]{\stepcounter{BonusCounter}
%  \arabic{BonusCounter}.~#1\\#2}

\begin{center}
  \includegraphics[scale=1]{acf-logo.pdf}\\
  {\sc 2014 ACF Nationals\\ Packet 1 by The Editors}
\end{center}
'''

latex_end = r'\end{document}'

ansregex = '(?i)a..?wers?:'
class InvalidPacket(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 80 + '\n'
        s += 'There was a problem in packet {0}\n'.format(self.args[0])
        s += '*' * 80 + '\n'

        return s

class InvalidTossup(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '\n'
        s += 'Invalid tossup {0}!\n'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}\n'.format(self.args[0], self.args[1])
        s += '*' * 50 + '\n'
        
        return s

class InvalidBonus(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '\n'
        s += 'Invalid bonus {0}!\n'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}\n'.format(self.args[0], self.args[1]) 
        s += '*' * 50 + '\n'
        
        return s

class Bonus:
    def __init__(self, leadin='', parts=[], answers=[], values=[], number=''):
        self.leadin = leadin
        self.parts = parts
        self.answers = answers
        self.number = number
        self.values = values
        
    def add_part(part):
        self.parts.append(part)

    def add_answer(answer):
        self.answers.append(answer)

    def to_json(self):
        return json.dumps({'leadin': self.leadin,
                           'parts': self.parts,
                           'answers': self.answers,
                           'number': self.number,
                           'values': self.values}) + '\n'

    def to_latex(self):
        leadin = self.leadin.replace('&ldquo;', '``')
        leadin = leadin.replace('&rdquo;', "''")
        leadin = leadin.replace('<i>', r'{\it ')
        leadin = leadin.replace('</i>', '}')
        leadin = r'\begin{{bonus}}{{{0}}}'.format(leadin) + '\n'
        parts = ''
        for val, part, answer in zip(self.values, self.parts, self.answers):
            answer = answer.replace('<req>', r'\ans{')
            answer = answer.replace('</req>', '}')
            answer = answer.replace('<b>', r'\ans{')
            answer = answer.replace('</b>', '}')
            answer = answer.replace('&ldquo;', '``')
            answer = answer.replace('&rdquo;', "''")
            part = part.replace('<i>', r'{\it ')
            part = part.replace('</i>', '}')
            part = part.replace('&ldquo;', '``')
            part = part.replace('&rdquo;', "''")
            
            parts += r'\bonuspart{{{0}}}{{{1}}}{{{2}}}'.format(val, part, answer) + '\n'
        return leadin + parts + r'\end{bonus}' + '\n'

    def is_valid(self):

        self.valid = False
        
        if self.leadin == '':
            raise InvalidBonus('leadin', self.leadin, self.number)
        if self.parts == []:
            raise InvalidBonus('parts', self.parts, self.number)
        if self.answers == []:
            raise InvalidBonus('answers', self.answers, self.number)
        if self.values == []:
            raise InvalidBonus('values', self.values, self.number)

        # for ans in self.answers:
        #    if re.match('answer:', ans) is None:
        #        raise InvalidBonus('answers', self.answers)
        #    if ans == '':
        #        raise Invalidbonus('answers', self.answers)

        for part in self.parts:
            if part == '':
                raise InvalidBonus('parts', self.parts, self.number)

        for val in self.values:
            if val == '':
                raise InvalidBonus('values', self.values, self.number)
            try:
                int(val)
            except ValueError:
                raise InvalidBonus('values', self.values, self.number)

        self.valid = True
        return True

    def __str__(self):

        s = '*' * 50 + '\n'
        s += self.leadin + '\n'

        for p, v, a in zip(self.parts, self.values, self.answers):
            s += '[{0}] {1}\nANSWER: {2}'.format(v, p, a)

        s += '*' * 50 + '\n'
        
        return s
        
class Tossup:
    def __init__(self, question='', answer='', number=''):
        self.question = question
        self.answer = answer
        self.number = number

    def to_json(self):
        return json.dumps({'question': self.question,
                           'answer': self.answer,
                           'number': self.number}) + '\n'

    def to_latex(self):
        answer = self.answer.replace('<req>', r'\ans{')
        answer = answer.replace('</req>', '}')
        answer = answer.replace('<b>', r'\ans{')
        answer = answer.replace('</b>', '}')
        question = self.question.replace('<i>', r'{\it ')
        question = question.replace('</i>', '}')
        answer = answer.replace('&ldquo;', '``')
        answer = answer.replace('&rdquo;', "''")
        question = question.replace('&ldquo;', '``')
        question = question.replace('&rdquo;', "''")
                
        return r'\tossup{{{0}}}{{{1}}}'.format(question, answer) + '\n'

    def is_valid(self):

        self.valid = False
        
        if self.question == '':
            raise InvalidTossup('question', self.question, self.number)

        if self.answer == '':
            raise InvalidTossup('answer', self.answer, self.number)

        # if re.match('answer:', self.answer) is None:
        #        raise InvalidTossup('answer', self.answer)

        self.valid = True
        return True

    def __str__(self):

        s = '*' * 50 + '\n'
        s += '{0}\nANSWER: {1}'.format(self.question, self.answer)
        s += '*' * 50 + '\n'

        return s
    
def empty_tags_left(soup):
    empty_tags = soup.findAll(lambda tag: (tag.string is None or tag.string.strip() == '') and tag.find(True) is None)
    print empty_tags
    if empty_tags == [] or empty_tags is None:
        return False
    else:
        return True
    
def sanitize (html, valid_tags):
    html = re.sub("\xa0", ' ', html)
    soup = BeautifulSoup(html)
    # get rid of comments
    for comment in soup.findAll(
        text=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True
    
    #print empty_tags_left(soup)
    
    # for some reason while doesn't work, not sure what's up
    for i in range(5):
        #empty_tags_left(soup)
        for tag in soup.findAll(lambda tag: (tag.string is None or tag.string.strip() == '') and tag.find(True) is None):
            tag.extract()

    #soup.encode('iso-8859-1')
    return soup.renderContents()
    #return soup.renderContents().decode('utf8').replace('javascript:', '')

def find_first_tossup (html):
    first_index = next((i for i in range(len(html)) if re.search(ansregex, html[i], re.I)), None)
    return first_index - 1

def find_first_bonus (html):
    first_index = next((i for i in range(len(html)) if re.search('^\[\w*\]|^\(\w*\)', html[i], re.I)), None)
    #this actually finds the first bonus part
    #so return that index - 1 to get the first bonus leadin
    return first_index - 1

def find_last_tossup (html, first_bonus_index):
    reversed = html[0:first_bonus_index][::-1]
    last_index = len(reversed) - find_first_tossup(reversed)
    return last_index - 1

def find_last_bonus (html):
    reversed = html[::-1]
    last_index = len(reversed) - find_first_bonus(reversed)
    return last_index

def packet_structured(tossups, bonuses, year=None, tournament=None, author=None, mode='json'):

    try:
        tossup_text, tossup_errors = tossups_structured(tossups, mode=mode)
        if tossup_errors > 0:
            raise InvalidPacket('{0} - {1}'.format(tournament, author))
    except InvalidPacket as ex:
        print ex
        
    try:    
        bonus_text, bonus_errors = bonuses_structured(bonuses, mode=mode)
        if bonus_errors > 0:
            raise InvalidPacket('{0} - {1}'.format(tournament, author))
    except InvalidPacket as ex:
        print ex

    if year is None:
        year = raw_input('Enter year: ')
    if tournament is None:
        tournament = raw_input('Enter tournament: ')
    if author is None:
        author = raw_input('Enter author: ')
    
    if mode == 'json':
        packet_text = '{"year": "' + str(year) + '", "tournament": "' + tournament + '", "author": "' + author + '", ' + tossup_text + ', ' + bonus_text + '}'
    elif mode == 'latex':
        packet_text = latex_preamble + tossup_text + bonus_text + latex_end

    return packet_text

def tossup_filter(tossups):

    tossups = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), tossups)
    #tossups = map(lambda text: re.sub('\'', '\\\'', text), tossups) 
    questions = [tossups[i] for i in range(len(tossups)) if i % 2 == 0]
    questions = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), questions)
    answers = [tossups[i] for i in range(len(tossups)) if i % 2 == 1]
    answers = [tossups[i] for i in range(len(tossups)) if i % 2 == 1]
    answers = map(lambda text: re.sub(ansregex, '', text, re.I), answers)
    answers = map(lambda text: string.strip(text), answers)
    answers = map(lambda text: sanitize(text, ['u', 'b']), answers)
    answers = map(lambda text: re.sub('(?i)<b><u>|<u><b>', '<req>', text), answers)
    answers = map(lambda text: re.sub('(?i)</b></u>|</u></b>', '</req>', text), answers)

    return tossups, questions, answers

def tossups_structured(tossups, mode='json'):

    errors = 0

    tossups, questions, answers = tossup_filter(tossups)

    tossups_text = ''
    
    for i, (question, answer) in enumerate(zip(questions, answers)):
        tossup = Tossup(question, answer, i + 1)
        if mode == 'json':
            tossups_text += tossup.to_json() + ','
        elif mode == 'latex':
            tossups_text += tossup.to_latex() + '\n'
        try:
            tossup.is_valid()
        except InvalidTossup as ex:
            print ex
            print tossup
            errors += 1

    if mode == 'json':
        tossups_text = '"tossups": [' + tossups_text[:-1] + ']' + '\n'
    elif mode == 'latex':
        tossups_text = r'\tossups' + '\n' + tossups_text[:-1] + '\n'

    return tossups_text, errors



def bonuses_structured(bonuses, mode='json'):

    errors = 0
    
    bonuses_text = ''
    bonuses = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), bonuses)
    #bonuses = map(lambda text: re.sub('\'', '\\\'', text), bonuses) 
    leadin_markers = [i for i in range(len(bonuses)) if not re.search('^\[\w*\]|^\(\w*\)|(?i)^(answer|asnwer|answers|anwer):', bonuses[i])]
    print leadin_markers
    for i in range(len(leadin_markers)):
        leadin = bonuses[leadin_markers[i]]
        parts = []
        values = []
        answers = []

        if leadin_markers[i] < leadin_markers[-1]:
            b_index = i + 1
            current_bonus = bonuses[leadin_markers[i] + 1:leadin_markers[b_index]]
        else:
            b_index = i
            current_bonus = bonuses[leadin_markers[b_index] + 1:]

            

        #print i, leadin_markers[i], b_index, leadin_markers[b_index]


        #print current_bonus
        for element in current_bonus:
            element = string.strip(element)
            if re.search(ansregex, element):
                answer = string.strip(re.sub(ansregex, '', element))
                answer = sanitize(answer, ['u', 'b'])
                answer = re.sub('(?i)<b><u>|<u><b>', '<req>', answer)
                answer = re.sub('(?i)</b></u>|</u></b>', '</req>', answer)
                answers.append(answer)
            else:
                match = re.search('^(\[\w*\]|\(\w*\))', element)
                val = re.sub('\[|\]|\(|\)', '', match.group(0))
                question = string.strip(re.sub('^(\[\w*\]|\(\w*\))', '', element))
                question = sanitize(question, ['i'])
                parts.append(question)
                values.append(val)

        bonus = Bonus(leadin, parts, answers, values, i + 1)
        if mode == 'json':
            bonuses_text += bonus.to_json() + ','
        elif mode == 'latex':
            bonuses_text += bonus.to_latex() + '\n'
        try:
            bonus.is_valid()
        except InvalidBonus as ex:
            print ex
            print bonus
            errors += 1
            
    if mode == 'json':
        bonuses_text = '"bonuses": [' + bonuses_text[:-1] + ']' + '\n'
    elif mode == 'latex':
        bonuses_text = r'\bonuses ' + '\n' + bonuses_text
    
    return bonuses_text, errors

def split_tossups_bonuses(doc_file):

    #curdir = os.path.curdir
    #os.chdir(os.path.abspath(doc_file))

    if doc_file.find('.docx') > -1:
        html_file = doc_file.replace('.docx', '.html')
    else:
        html_file = doc_file.replace('.doc', '.html')
    valid_tags = ['em', 'strong', 'b', 'i', 'u']
    
    import platform
    if platform.system() == 'Linux':
        #cmd = 'unoconv -f html -o "' + html_file + '" "' + doc_file + '"'
        #valid_tags.append('p')
        cmd = 'pandoc -f docx -t html -o "{0}" "{1}"'.format(html_file, doc_file)
    if platform.system() == 'Darwin':
        cmd = 'pandoc -f docx -t html -o "{0}" "{1}"'.format(html_file, doc_file)
        # cmd = 'textutil -convert html \"' + doc_file + '\"'

    cmd = shlex.split(cmd)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    
    # print doc_file, html_file
    f = open(html_file, 'r')

    html = ''
    
    for line in f.readlines():
        html += line
    f.close()

    #html = sanitize(html, valid_tags).split('\n')
    html = re.compile('\n|\r\n').split(sanitize(html, valid_tags))
    html = map(lambda text: string.strip(text), html)

    html = filter(lambda text: text != '' and not text.startswith('TIEBREAKER'), html)
    html = re.sub('([^\n])(ANSWER|\[\d+\])', '\\1\n\\2', '\n'.join(html)).split('\n')
    html = map(string.strip, html)

    f = open(html_file, 'w')
    for line in html:
        f.write(line + '\n')

    f.close()

    return handle_html(html_file)


def handle_html(html_file):
    f = open(html_file, 'r')
    print html_file
    html = []
    for line in f:
        html.append(line)

    #html = f.readlines()

    #print html

    first_tossup = find_first_tossup(html)
    first_bonus = find_first_bonus(html)

    last_tossup = find_last_tossup(html, first_bonus)
    last_bonus = find_last_bonus(html)

    tossups = html[first_tossup:last_tossup]
    bonuses = html[first_bonus:last_bonus]
    
    #print last_bonus

    cleaned_tossups = [line for line in tossups if len(line) > 7]
    cleaned_bonuses = [line for line in bonuses if len(line) > 7]
    
    cleaned_tossups = map(lambda text: string.strip(re.sub('<u></u>', '', text, re.I)), cleaned_tossups)          
    cleaned_tossups = map(lambda text: string.strip(re.sub('<b></b>', '', text, re.I)), cleaned_tossups)
    cleaned_tossups = map(lambda text: string.strip(re.sub('<u></u>', '', text, re.I)), cleaned_tossups)
    cleaned_tossups = map(lambda text: string.strip(re.sub('<b></b>', '', text, re.I)), cleaned_tossups)
    
    cleaned_bonuses = map(lambda text: string.strip(re.sub('<u></u>', '', text, re.I)), cleaned_bonuses)          
    cleaned_bonuses = map(lambda text: string.strip(re.sub('<b></b>', '', text, re.I)), cleaned_bonuses)
    cleaned_bonuses = map(lambda text: string.strip(re.sub('<u></u>', '', text, re.I)), cleaned_bonuses)
    cleaned_bonuses = map(lambda text: string.strip(re.sub('<b></b>', '', text, re.I)), cleaned_bonuses)

    return cleaned_tossups, cleaned_bonuses

def process_dir_super(doc = True):
    ext = 'doc' if doc else 'html'
    file_fn = split_tossups_bonuses if doc else handle_html
    print ext
    def process_dir(arg, dirname, fnames):
        fnames = filter(lambda text: re.search('\.'+ext, text), fnames)
        tournament_json = ''
        conf = None
        
        num_packets = len(fnames)
        
        if fnames == []:
            return

        conf_path = os.path.join(dirname, 'config.json')
        
        if os.path.exists(conf_path):
            conf = json.load(open(conf_path, 'r'))
        else:
            #shouldn't go down here if we're reading html files
            conf_file = conf_gen(dirname, '*.doc')
            conf = json.load(open(conf_file, 'r'))

        if conf:
            year = conf['year']
            tournament = conf['tournament']

            for packet in conf['packets']:
                filename = os.path.splitext(packet['filename'])[0] + '.' + ext
                author = packet['author']
                
                tossups, bonuses = file_fn(os.path.join(dirname, filename))
                tournament_json += packet_structured(tossups, bonuses, year, tournament, author) + ','
            
        else:
            year = raw_input('Enter year: ')
            tournament = raw_input ('Enter tournament: ')
        
            for fname in fnames:
                print fname
                filename = os.path.join(os.path.abspath(dirname), fname)
            
                author = raw_input('Enter author: ')

                tossups, bonuses = file_fn(filename)
                tournament_json += packet_structured(tossups, bonuses, year, tournament, author) + ','
            
        tournament_json = '{"tournament": "' + tournament +\
         '", "year": "' + str(year) +\
         '", "numPackets": "' + str(num_packets) +\
         '", "packets": [' + tournament_json[:-1] + '] }'
        
        tournament_json_file = os.path.join(dirname, '{0} - {1}.json'.format(year, tournament))

        file = open(tournament_json_file, 'w')
        file.write(tournament_json)
        file.close()
        #json.dump(tournament_json, open(tournament_json_file, 'w+'))
        
        print 'Tournament exported to ' + tournament_json_file
    return process_dir

def conf_gen(path, spec):

    os.chdir(path)
    files = glob.glob(spec)

    output_file = open('config.json', 'w+')

    tour_dict = {}
    
    tour_dict['tournament']  = raw_input('Enter tournament: ')
    tour_dict['year'] = raw_input('Enter year: ')

    tour_dict['packets'] = []
    
    for filename in files:
        author = raw_input('Enter the author of {0}: '.format(filename))
        tour_dict['packets'].append({'filename': filename, 'author': author})

    json.dump(tour_dict, output_file)

    print 'dumped config to ' + os.path.join(path, 'config.json')

    return os.path.abspath('config.json')
    
def validate_json(filename):

    try:
        json.load(open(filename, 'r'))
        print "Valid JSON!"
        return True
    except Exception as ex:
        print "Invalid JSON!"
        print ex
        return False

def latexify(filename):

    tossups, bonuses = split_tossups_bonuses(filename)
    output_file = filename.replace('.doc', '.tex')
    
    


def import_json_into_mongo(filename):

    if not validate_json(filename):
        print 'You have some problems in your JSON file. Correct them and try again.'
        return
    else:
        tournament_json = json.load(open(filename, 'r'))

        tournament = tournament_json['tournament']
        year = tournament_json['year']
        packets_json = tournament_json['packets']
        
        num_packets = len(packets_json)
        
        print 'importing ' + tournament
        
        t_id = tournaments.insert({'tournament': tournament, 'year': year, 'numPackets': num_packets})
       
                
        for packet in packets_json:

            print 'importing packet ' + packet['author']
            
            p_id = packets.insert({'tournament_name': packet['tournament'],
                                   'year': packet['year'], 
                                   'author': packet['author'], 
                                   'tournament': t_id})


            tossups_json = packet['tossups']
            bonuses_json = packet['bonuses']

            for tossup in tossups_json:
                tossup_id = tossups.insert({'question': tossup['question'],
                                            'answer': tossup['answer'],
                                            'packet': p_id,
                                            'tournament': t_id})

            for bonus in bonuses_json:
                bonus_id = bonuses.insert({'leadin': bonus['leadin'],
                                           'part' :  bonus['parts'],
                                           'value' : bonus['values'],
                                           'answer': bonus['answers'],
                                           'packet': p_id,
                                           'tournament': t_id})
    
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
            tossups, bonuses = split_tossups_bonuses(args.file)
            #print bonuses
            packet_structured = packet_structured(tossups, bonuses, mode=args.mode)
            
            if args.output_file is not None:
                f = open(args.output_file, 'w')
                f.write(packet_structured)
                f.close()
            else:
                print packet_structured
                pass
            

        if args.operation == 'validate':
            validate_json(args.file)

        if args.operation == 'import':
            import_json_into_mongo(args.file)

    if args.operation == 'conf' and args.dir is not None and args.spec is not None:
        conf_gen(args.dir, args.spec)
