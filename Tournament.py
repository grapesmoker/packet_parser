from Packet import Packet, InvalidPacket
from utils import conf_gen

import re
import os
import json

class Tournament:

    def __init__(self, tour_name=None, year=None, packets=[]):
        self.tour_name = tour_name
        self.year = year
        self.packets = packets
        
    def add_packet(self, packet):
        self.packets.append(packet)

    def to_dict(self):

        tour_dict = {'tournament': self.tour_name,
                     'year': self.year,
                     'packets': [packet.to_dict() for packet in self.packets]}

        return tour_dict

    def to_json(self):

        return json.dumps(self.to_dict(), indent=4)

    def __str__(self):

        return '{0} {1}'.format(self.tour_name, self.year)

    def is_valid(self):

        packet_errors = []
        for packet in self.packets:
            try:
                if packet.is_valid():
                    pass
            except InvalidPacket as ex:
                packet_errors.append(ex)

        if packet_errors == []:
            return True
        else:
            for err in packet_errors:
                print err
            return False

    def create_tournament_from_directory(self, dir):

        conf_file = os.path.join(dir, 'config.json')

        if not os.path.exists(conf_file):
            conf_file = conf_gen(dir, '*.docx')

        conf_dict = json.load(open(conf_file, 'r'))

        self.tour_name = conf_dict['tournament']
        self.year = conf_dict['year']

        packets = conf_dict['packets']

        for file_entry in packets:
            packet_file = os.path.join(dir, file_entry['filename'])
            packet_author = file_entry['author']

            packet = Packet(packet_author, tournament=self.tour_name)
            packet.load_packet_from_file(packet_file)

            self.add_packet(packet)