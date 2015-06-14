from bs4 import BeautifulSoup, Comment
import re
import os
import glob
import json

ansregex = '(?i)a..?wers?:'
bpart_regex = '^[\s]*\[\d+\]'
bonus_value_regex = '\[|\]|\(|\)'

def is_answer(line):

    return re.search(ansregex, line) is not None

def is_bpart(line):
    
    return re.search(bpart_regex, line) is not None

def get_bonus_part_value(line):
    
    match = re.search(bpart_regex, line)
    return re.sub(bonus_value_regex, '', match.group(0))

def sanitize (html, valid_tags=[]):
    soup = BeautifulSoup(html)
    # get rid of comments
    for comment in soup.findAll(
        text=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True

    return soup.renderContents().decode('utf8')

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

    output_file.close()

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
                
def tossup_filter(tossups):

    tossups = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), tossups)
    #tossups = map(lambda text: re.sub('\'', '\\\'', text), tossups) 
    questions = [tossups[i] for i in range(len(tossups)) if i % 2 == 0]
    questions = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), questions)
    answers = [tossups[i] for i in range(len(tossups)) if i % 2 == 1]
    answers = map(lambda text: re.sub(ansregex, '', text, re.I), answers)
    answers = map(lambda text: string.strip(text), answers)
    answers = map(lambda text: sanitize(text, ['u', 'b']), answers)
    answers = map(lambda text: re.sub('(?i)<b><u>|<u><b>', '<req>', text), answers)
    answers = map(lambda text: re.sub('(?i)</b></u>|</u></b>', '</req>', text), answers)

    return tossups, questions, answers
