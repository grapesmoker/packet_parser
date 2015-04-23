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

    def __unicode__(self):

        s = '*' * 50 + '\n'
        s += self.leadin + '\n'

        for p, v, a in zip(self.parts, self.values, self.answers):
            s += '[{0}] {1}\nANSWER: {2}'.format(v, p, a)

        s += '*' * 50 + '\n'
        
        return s.decode('utf-8')
