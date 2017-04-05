from Tossup import Tossup, InvalidTossup
from Bonus import Bonus, InvalidBonus

import json
import re
import os
import shlex
import subprocess
import codecs

from utils import ansregex, bpart_regex, is_answer, is_bpart, get_bonus_part_value, sanitize, conf_gen


class InvalidPacket(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '\nThere was a problem in packet {0}\n\n'.format(self.args[0])
        for err in self.args[1]:
            s += '\n' + str(err)
        for err in self.args[2]:
            s += '\n' + str(err)    

        return s


class PacketParserError(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        return'\nThere was a problem parsing packet {}!\nInvalid data encountered near: {}'.format(self.args[0], self.args[1])


class Packet:

    def __init__(self, author, tossups=None, bonuses=None, tournament=None):
        self.author = author
        if tossups:
            self.tossups = tossups
        else:
            self.tossups = []

        if bonuses:
            self.bonuses = bonuses
        else:
            self.bonuses = []

        self.tournament = tournament

    def add_tossup(self, tossup):

        self.tossups.append(tossup)

    def add_bonus(self, bonus):

        self.bonuses.append(bonus)

    def __unicode__(self):

        return 'Packet by {0}'.format(self.author)

    def __str__(self):

        return 'Packet by {0}'.format(self.author)

    def to_dict(self):

        packet = {}
        packet['author'] = self.author
        packet['tossups'] = []
        packet['bonuses'] = []

        for tossup in self.tossups:
            packet['tossups'].append(tossup.to_dict())

        for bonus in self.bonuses:
            packet['bonuses'].append(bonus.to_dict())

        return packet

    def to_json(self):

        return json.dumps(self.to_dict(), indent=4)

    def is_valid(self):

        tossup_errors = []
        bonus_errors = []
        
        if self.tossups == [] and self.bonuses == []:
            raise InvalidPacket(self.author, [], [])
        
        for tossup in self.tossups:
            try:
                tossup.is_valid()
            except InvalidTossup as ex:
                tossup_errors.append(ex)

        for bonus in self.bonuses:
            try:
                bonus.is_valid()
            except InvalidBonus as ex:
                bonus_errors.append(ex)

        if tossup_errors != [] or bonus_errors != []:
            raise InvalidPacket(self.author, tossup_errors, bonus_errors)
        else:
            print('packet {0} parsed {1} tossups and {2} bonuses'.format(self.author, len(self.tossups), len(self.bonuses)))
            return True

    def load_packet_from_file(self, doc_file, reuse_html=False, test=False):

        if reuse_html:
            if re.search('docx', doc_file):
                html_file = doc_file.replace('.docx', '.html')
            elif re.search('doc', doc_file):
                html_file = re.sub('doc', 'html', doc_file)
            else:
                raise ValueError("not valid input format!")
            with open(html_file, 'r') as f:
                packet_contents = f.read().split('\n')
        else:
            html_file = self.convert_doc_to_html(doc_file, test)
            packet_contents = self.prepare_html_file(html_file)

        tossups, bonuses = self.parse_packet(packet_contents)

        self.tossups = tossups
        self.bonuses = bonuses

    def convert_doc_to_html(self, doc_file, test=False):
        
        doc_file = os.path.abspath(doc_file)
        
        if re.search('docx', doc_file):
            html_file = doc_file.replace('.docx', '.html')
        elif re.search('doc', doc_file):
            html_file = re.sub('doc', 'html', doc_file)
        else:
            print("not valid input format")

        if test:
            html_file = '/Users/vinokurovy/Development/personal/packet_parser/test.html'
        
        cmd = 'pandoc -f docx -t html -o "{0}" "{1}"'.format(html_file, doc_file)
        cmd = shlex.split(cmd)
    
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
    
        return html_file

    def prepare_html_file(self, html_file, skip_lines=0):
    
        with codecs.open(html_file, 'r', encoding='utf-8') as f:
            packet_contents = f.read()

        packet_contents = re.sub('<br />', '', packet_contents)
            
        packet_contents = [sanitize(element, valid_tags=['em', 'strong']) for element in packet_contents.split('\n')]

        # import ipdb; ipdb.set_trace()

        tossups_start = None
        bonuses_start = None
        for i, item in enumerate(packet_contents):
            if re.search('Tossups', item, flags=re.I) and not tossups_start:
                tossups_start = i + 1
            elif re.search('Bonuses', item, flags=re.I) and not bonuses_start:
                bonuses_start = i

        #print(tossups_start, bonuses_start)

        if tossups_start is not None and bonuses_start is not None:
            tossups = packet_contents[tossups_start:bonuses_start]
            bonuses = packet_contents[bonuses_start + 1:]
            packet_contents = tossups + bonuses
            #print(html_file, '\n', tossups[-1], '\n', bonuses[0], '\n', bonuses[-1])
            #print(bonuses[0])
            #print(bonuses[-1])

        packet_contents = [x.strip() for x in packet_contents if sanitize(x).strip() != ''
                           and len(x) > 20
                           and not x.strip() in ['Extra', 'Extras']
                           and not re.search('^(<.*>|&lt;.*&gt;)', x.strip())]

        with open(html_file, 'w') as f:
            for item in packet_contents:
                f.write(item + '\n')

        return packet_contents[skip_lines:]

    def parse_packet(self, packet_contents):
    
        parser_stack = []
    
        tossups = []
        bonuses = []

        tu_num = 1
        bs_num = 1

        # this is an arbitrary symbol to make sure the stack popping terminates
        packet_contents.append(50 * '*')

        # import ipdb; ipdb.set_trace()

        for i, item in enumerate(packet_contents, start=1):
        
            if (not is_answer(item) and not is_bpart(item) and not len(parser_stack) < 2) or i == len(packet_contents):
                # pop the stack
                result = []
                while parser_stack != []:
                    result.append(parser_stack.pop())
                result.reverse()
        
                if len(result) == 2 and is_answer(result[1]) and not is_answer(result[0]) and not is_bpart(result[0]):
                    answer = re.sub(ansregex, '', result[1])
                    question = result[0]
                    new_tossup = Tossup(question=question, answer=answer, number=tu_num,
                                        packet=self.author, tournament=self.tournament)
                    tossups.append(new_tossup)
                    #print(tu_num, answer)
                    tu_num += 1
                    
                elif len(result) > 2 and (len(result) % 2 == 1) and is_answer(result[-1]) and not is_answer(result[0]):
                    bonus_parts = result[1::2]
                    values = []
                    for bp in bonus_parts:
                        try:
                            val = int(get_bonus_part_value(bp))
                        except Exception as ex:
                            print('Could not extract value from\n{0}\n in \n{1}, assuming 10'.format(bp, self.author))
                            val = 10
                        values.append(val)
                        
                    bonus_parts = [re.sub(bpart_regex, '', part).strip() for part in bonus_parts]
                    answers = [re.sub(ansregex, '', ans).strip() for ans in result[2::2]]
                    leadin = result[0]

                    if len(answers) > 3 and len(bonus_parts) > 3:
                        raise PacketParserError(self.author, result)

                    bonus = Bonus(leadin=leadin, parts=bonus_parts,
                                  values=values, answers=answers, number=bs_num,
                                  packet=self.author, tournament=self.tournament)
                    bonuses.append(bonus)
                    bs_num += 1
                elif len(result) > 2:
                    raise PacketParserError(self.author, result)

                parser_stack.append(item)
            else:
                parser_stack.append(item)
                
        return tossups, bonuses
