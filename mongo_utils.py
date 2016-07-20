import pymongo

from pymongo import MongoClient

try:
    conn = MongoClient('localhost', 27017)
    db = conn.qbdb
    tournaments = db.tournaments
    packets = db.packets
    tossups = db.tossups
    bonuses = db.bonuses

except Exception as ex:
    print 'Mongo not available'

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
