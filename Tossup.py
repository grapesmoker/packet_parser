from utils import sanitize
import re
num_regex = '^<strong>[\d]+\.[\s]*<\/strong>[\s]*'
tb_regex = '^<strong>TB\.[\s]*<\/strong>[\s]*'

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
    def __init__(self, question='', answer='', number=''):
        self.question = question
        self.answer = answer
        self.number = number
        
        self.answer_sanitized = sanitize(self.answer, [])
        self.question_sanitized = sanitize(self.question, [])

        self.question = re.sub(num_regex, '', self.question)
        self.question = re.sub(tb_regex, '', self.question)
        
        self.answer = self.answer.replace('<strong><em>', '<req>')
        self.answer = self.answer.replace('<em><strong>', '<req>')
        self.answer = self.answer.replace('</em></strong>', '</req>')
        self.answer = self.answer.replace('</strong></em>', '</req>')

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

    def __unicode__(self):

        s =  '\n' #'*' * 50 + '\n'
        s += '{0}\nANSWER: {1}'.format(self.question, self.answer)
        s += '\n' #'*' * 50 + '\n'

        return s.decode('utf-8')
