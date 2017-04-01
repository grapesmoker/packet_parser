import re
import json

from utils import sanitize

num_regex = '^([\s]*<strong>[\d]+\.[\s]*<\/strong>[\s]*|[\s]*[\d]+\.[\s]*)'
tb_regex = '^([\s]*<strong>TB\.[\s]*<\/strong>[\s]*|[\s]*TB\.[\s]*)'

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

    def __init__(self, leadin='', parts=None, answers=None, values=None, number='',
                 packet=None, tournament=None):
        self.leadin = leadin
        if parts: self.parts = parts
        else: self.parts = []

        if answers: self.answers = answers
        else: self.answers = []

        if values: self.values = values
        else: self.values = []

        self.number = number
        self.packet = packet
        self.tournament = tournament

        self.leadin = re.sub(num_regex, '', self.leadin)
        self.leadin = re.sub(tb_regex, '', self.leadin)
        
        if self.leadin.startswith('<strong>'):
            self.leadin = '<strong>' + re.sub('^[\d]+\.[\s]*', '', self.leadin[8:])
            self.leadin = '<strong>' + re.sub('^TB\.[\s]*', '', self.leadin[8:])

        def clean_answer(ans):
            ans = ans.replace('<strong><em>', '<req>')
            ans = ans.replace('<em><strong>', '<req>')
            ans = ans.replace('</em></strong>', '</req>')
            ans = ans.replace('</strong></em>', '</req>')
            return ans

        self.answers = [clean_answer(answer) for answer in self.answers]
        self.answers_sanitized = [sanitize(answer) for answer in self.answers]
        self.leadin_sanitized = sanitize(self.leadin)
        self.parts_sanitized = [sanitize(part) for part in self.parts]
        
    def add_part(self, part):
        self.parts.append(part)

    def add_answer(self, answer):
        self.answers.append(answer)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4) + '\n'

    def to_dict(self):
        return {'leadin': self.leadin,
                'parts': self.parts,
                'answers': self.answers,
                'number': self.number,
                'values': self.values,
                'leadin_sanitized': self.leadin_sanitized,
                'parts_sanitized': self.parts_sanitized,
                'answers_sanitized': self.answers_sanitized,
                'packet': self.packet,
                'tournament': self.tournament}

    
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

        if len(self.parts) != len(self.values):
            raise InvalidBonus('parts and values', (self.parts, self.values), self.number)
        elif len(self.parts) != len(self.answers):
            raise InvalidBonus('parts and answers', (self.parts, self.values), self.number)
        elif len(self.values) != len(self.answers):
            raise InvalidBonus('values and answers', (self.values, self.answers), self.number)

        if len(self.parts) == 1:
            # this should never happen
            raise InvalidBonus('parts', self.parts, self.number)

        self.valid = True
        return True

    def __unicode__(self):
        s = self.leadin + '\n'

        for p, v, a in zip(self.parts, self.values, self.answers):
            s += '[{0}] {1}\nANSWER: {2}\n'.format(v, p, a)

        return s

    def __str__(self):

        return self.__unicode__()
