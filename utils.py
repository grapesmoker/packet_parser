from bs4 import BeautifulSoup, Comment
import re
import os
import glob
import json
import string

from time import sleep

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
    soup = BeautifulSoup(html, 'lxml')
    # get rid of comments
    for comment in soup.findAll(
        text=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True

    return soup.renderContents().decode('utf8')


def conf_gen(path, spec):

    old_dir = os.path.abspath(os.curdir)
    os.chdir(path)
    files = glob.glob(spec)

    tour_dict = {}

    tournament = os.path.split(path)[-1]
    year_guess = None
    tournament_guess = None
    year_match = re.search('[\d]{4}', tournament)
    if year_match:
        year_guess = tournament[year_match.start():year_match.end()]
        tournament_guess = tournament[year_match.end() + 1:]

    print(tournament_guess)
    print(year_guess)
    print(path)

    tournament_name = input('Enter tournament [default: {}]: '.format(tournament_guess))
    if str(tournament_name) == '':
        tournament_name = tournament_guess

    year = input('Enter year [default: {}]: '.format(year_guess))
    if str(year) == '':
        year = year_guess

    tour_dict['tournament'] = tournament_name
    tour_dict['year'] = year

    tour_dict['packets'] = []
    
    for filename in files:
        if '-' in filename:
            split_fn = filename.split('-')
            if len(split_fn) == 2:
                author_guess = filename.split('-')[1].strip().replace('.docx', '')
            elif len(split_fn) > 2:
                author_guess = ' - '.join(split_fn[1:]).strip().replace('.docx', '')
        else:
            author_guess = filename
        author = input('Enter the author of {} [default: {}]: '.format(filename, author_guess))
        if str(author) == '':
            author = author_guess
        tour_dict['packets'].append({'filename': filename, 'author': author})

    output_file = open('config.json', 'w+')
    json.dump(tour_dict, output_file, indent=4)

    print('dumped config to ' + os.path.join(path, 'config.json'))

    output_file.close()

    conf_path = os.path.abspath('config.json')
    os.chdir(old_dir)
    return conf_path


def validate_json(filename):

    try:
        json.load(open(filename, 'r'))
        print("Valid JSON!")
        return True
    except Exception as ex:
        print("Invalid JSON!")
        print(ex)
        return False


def tossup_filter(tossups):

    #tossups = map(lambda text: re.sub('^\d*\.', '', text).strip(), tossups)
    tossups = [re.sub('^\d*\.', '', text).strip() for text in tossups]
    questions = [tossups[i] for i in range(len(tossups)) if i % 2 == 0]
    #questions = map(lambda text: (re.sub('^\d*\.', '', text)).strip(), questions)
    questions = [re.sub('^\d*\.', '', text).strip() for text in questions]
    answers = [tossups[i] for i in range(len(tossups)) if i % 2 == 1]
    answers = list(map(lambda text: re.sub(ansregex, '', text, re.I), answers))
    answers = list(map(lambda text: text.strip(), answers))
    answers = list(map(lambda text: sanitize(text, ['u', 'b']), answers))
    answers = list(map(lambda text: re.sub('(?i)<b><u>|<u><b>', '<req>', text), answers))
    answers = list(map(lambda text: re.sub('(?i)</b></u>|</u></b>', '</req>', text), answers))

    return tossups, questions, answers
