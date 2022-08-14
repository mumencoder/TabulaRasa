
import sys
import kafka
import json
import base64, binascii

from packets import *

args = {"since":0, "character":"Smolcat", "id_lo":None, "id_hi":None}

packet_parsers = {}
packet_parsers['lobby-data-in'] = parse_lobby_data_c2s
packet_parsers['lobby-data-out'] = parse_lobby_data_s2c
packet_parsers['lobby-view-in'] = parse_lobby_view_c2s
packet_parsers['lobby-view-out'] = parse_lobby_view_s2c

def get_events(topics):
  parts = [kafka.TopicPartition(topic, 0) for topic in topics]
  consumer = kafka.KafkaConsumer(bootstrap_servers='172.31.177.56:9092')
  consumer.assign(parts)
  for part in parts:
    consumer.seek(part, 0)

  events = []
  while True:
    results = consumer.poll(timeout_ms=50)
    if len(results) == 0:
      break
    for msgs in results.values():
      for msg in msgs:
        events.append( {"msg":msg, "value":json.loads(msg.value)})
  return events

def lobby_topics():
  topics = ['lobby-data-in', 'lobby-data-out', 'lobby-view-in', 'lobby-view-out', 'lobby-socket']
  events = get_events(topics)
    
  for event in sorted( events, key=lambda event: event["value"]["id"] ):
    print( event["value"] )
    if event["msg"].topic in ['lobby-data-in', 'lobby-data-out', 'lobby-view-in', 'lobby-view-out']:
      event["value"]["data"] = base64.b64decode( event["value"]["data"])
#      if event["value"]["socket"]["client_addr"] != '172.27.0.8':
#        continue
      if len(event["value"]["data"]) == 0:
        continue 
      print("==========================")
      print( event["value"]["data"] )
      ppacket = packet_parsers[event["msg"].topic]( event["value"]["data"] )
      print( event["msg"].topic, ppacket.unknown_str )
      #print( event["msg"].topic, ppacket.full_packet )

def map_topics():
  topics = ['packets-in', 'packets-out']
  events = get_events(topics)

  for event in sorted( events, key=lambda event: event["value"]["id"] ):
    if float(event["value"]["timestamp"]) < float(args["since"]):
      continue
    if event["value"]["character"]["name"] != args["character"]:
      continue
    epacket = event["value"]["packet"]
    epacket["type"] = int( epacket["type"] )
    epacket["hextype"] = hex( epacket["type"] )
    del epacket["data"]
    if event["msg"].topic == "packets-out":
      epacket["desc"] = MapPacket.s2c[ epacket["type"] ]["descs"]
    del epacket["type"]
    del event["value"]["session"]
    del event["value"]["character"]
    print(event["msg"].topic, event["value"])

#lobby_topics()    
map_topics()