
from common import *
from client.packets import *

args = {}
args = {"since":0, "character":"Smolcat", "id_lo":None, "id_hi":None}
#args = {"since":0, "character":"Noocat", "id_lo":None, "id_hi":None}
#args = {"since":0, "character":"GilaFirthimi", "id_lo":None, "id_hi":None}
#args = {"since":0, "character":"EMhaarra", "id_lo":None, "id_hi":None}

#packet_parsers = {}
#packet_parsers['lobby-data-in'] = parse_lobby_data_c2s
#packet_parsers['lobby-data-out'] = parse_lobby_data_s2c
#packet_parsers['lobby-view-in'] = parse_lobby_view_c2s
#packet_parsers['lobby-view-out'] = parse_lobby_view_s2c

#msg_start = 0
msg_start = (time.time() - 1200) * 1000
msg_stop = time.time() * 1000

def get_events(topics):
    parts = [kafka.TopicPartition(topic, 0) for topic in topics]
    consumer = kafka.KafkaConsumer(bootstrap_servers='172.31.177.56:9092')
    consumer.assign(parts)

    partstamps = {part:msg_start for part in parts}
    stamps = consumer.offsets_for_times(partstamps)
    for part, stamp in stamps.items():
        consumer.seek(part, stamp.offset)

    events = []
    topic_done = set()
    while len(topic_done) != len(parts):
        results = consumer.poll(timeout_ms=10000)
        if len(results) == 0:
            break
        for msgs in results.values():
            for msg in msgs:
                if msg.timestamp > msg_stop:
                    topic_done.add( msg.topic )
                    break
                events.append( {"msg":msg, "value":json.loads(msg.value)})

    print("events:", len(events))
    return events

def lobby_topics():
    topics = ['lobby-data-in', 'lobby-data-out', 'lobby-view-in', 'lobby-view-out', 'lobby-socket']
    events = get_events(topics)

    for event in sorted( events, key=lambda event: event["value"]["id"] ):
        msg = event["msg"]
        value = event["value"]
        print(event["value"])

def map_topics():
    topics = ['packets-in', 'packets-out']
    events = get_events(topics)

    for event in sorted( events, key=lambda event: event["msg"].timestamp ):
        msg = event["msg"]
        value = event["value"]
        if "character" in args and value["character"]["name"] != args["character"]:
            continue
        epacket = value["packet"]
        epacket["type"] = int( epacket["type"] )
        epacket["hextype"] = hex( epacket["type"] )

        if epacket["type"] == 386:
            continue
        if msg.topic == "packets-out":
            epacket["desc"] = MapPacket.s2c[ epacket["type"] ]["descs"]
        if msg.topic == "packets-in":
            epacket["desc"] = MapPacket.c2s[ epacket["type"] ]["descs"]

        if msg.topic == "packets-in" and epacket['hextype'] == '0x15':
            pass
        elif msg.topic == "packets-out" and epacket['hextype'] == '0xdf':
            #print("0xdf", pprint_packet( base64.b64decode(  epacket["data"]) ) )
            pass
        elif msg.topic == "packets-out" and epacket['hextype'] == '0x37':
            #print("0x37", pprint_packet( base64.b64decode(  epacket["data"]) ) )
            pass
        elif msg.topic == "packets-out" and epacket['hextype'] == '0xe':
            pass
        else:
            del epacket["data"]
            del epacket["type"]
            del value["session"]
            print(msg.topic, value)
        

#lobby_topics()    
map_topics()