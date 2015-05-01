from utils import sanitize
import re
import json

num_regex = '^(<strong>[\d]+\.[\s]*<\/strong>[\s]*|[\d]+\.[\s]*)'
tb_regex = '^(<strong>TB\.[\s]*<\/strong>[\s]*|TB\.[\s]*)'

class InvalidTossup(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '\n'
        s += 'Invalid tossup {0}!\n'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}\n'.format(self.args[0], self.args[1])
        s += '*' * 50 + '\n'
        
        return s.decode('utf-8')

class Tossup:
    def __init__(self, question='', answer='', number='', packet=None, tournament=None):
        self.question = question
        self.answer = answer
        self.number = number
        
        self.answer_sanitized = sanitize(self.answer, [])
        self.question_sanitized = sanitize(self.question, [])

        self.question = re.sub(num_regex, '', self.question)
        self.question = re.sub(tb_regex, '', self.question)

        if self.question.startswith('<strong>'):
            self.question = '<strong>' + re.sub('^[\d]+\.[\s]*', '', self.question[8:])
            self.question = '<strong>' + re.sub('^TB\.[\s]*', '', self.question[8:])
        
        self.answer = self.answer.replace('<strong><em>', '<req>')
        self.answer = self.answer.replace('<em><strong>', '<req>')
        self.answer = self.answer.replace('</em></strong>', '</req>')
        self.answer = self.answer.replace('</strong></em>', '</req>')

        self.packet = packet
        self.tournament = tournament

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4) + '\n'

    def to_dict(self):
        return {'question': self.question,
                'answer': self.answer,
                'number': self.number,
                'answer_sanitized': self.answer_sanitized,
                'question_sanitized': self.question_sanitized,
                'packet': self.packet,
                'tournament': self.tournament}


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

    def __unicode__(self):

        s =  '\n' #'*' * 50 + '\n'
        s += '{0}\nANSWER: {1}'.format(self.question, self.answer)
        s += '\n' #'*' * 50 + '\n'

        return s.decode('utf-8')

    def __str__(self):

        return self.__unicode__()
