
#include "common/base64.h"
#include "common/json.hpp"
#include "kafka.h"

static rd_kafka_t* kafka_producer;
static rd_kafka_conf_t* kafka_conf;
static int msg_id = 0;

void kafka_init() {
    char errstr[256];
    kafka_conf = rd_kafka_conf_new();
    rd_kafka_conf_set(kafka_conf, "bootstrap.servers", "broker:9092", errstr, sizeof(errstr));
    kafka_producer = rd_kafka_new(RD_KAFKA_PRODUCER, kafka_conf, errstr, sizeof(errstr));
}

using nlohmann::json;

void log_map_packet_out(map_session_data_t* const PSession, CCharEntity* const PChar, CBasicPacket data) {
    json msg, session, packet, character;
    character["name"] = (char*)PChar->GetName();
    session["client_addr"] = ip2str(PSession->client_addr);
    session["client_port"] = PSession->client_port;
    packet["type"] = data.getType();
    packet["size"] = data.getSize();
    packet["data"] = base64_encode( (uint8*)data, data.getSize() );
    msg["timestamp"] = time(nullptr);
    msg["session"] = session;
    msg["packet"] = packet;
    msg["character"] = character;
    msg["id"] = msg_id;
    msg_id += 1;
    std::string msgStr = msg.dump();
    rd_kafka_producev(kafka_producer,
        RD_KAFKA_V_TOPIC("packets-out"),
        RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
        RD_KAFKA_V_KEY( (void*)"packet", strlen("packet")),
        RD_KAFKA_V_VALUE( (void*)msgStr.c_str(), msgStr.length() ),
        RD_KAFKA_V_END
    );
    //rd_kafka_flush(kafka_producer, 50);
}

void log_map_packet_in(map_session_data_t* const PSession, CCharEntity* const PChar, CBasicPacket data) {
    json msg, session, packet, character;
    character["name"] = (char*)PChar->GetName();
    session["client_addr"] = ip2str(PSession->client_addr);
    session["client_port"] = PSession->client_port;
    packet["type"] = data.getType();
    packet["size"] = data.getSize();
    packet["data"] = base64_encode( (uint8*)data, data.getSize() );
    msg["id"] = msg_id;
    msg_id += 1;
    msg["character"] = character;
    msg["timestamp"] = time(nullptr);
    msg["session"] = session;
    msg["packet"] = packet;
    std::string msgStr = msg.dump();
    rd_kafka_producev(kafka_producer,
        RD_KAFKA_V_TOPIC("packets-in"),
        RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
        RD_KAFKA_V_KEY( (void*)"packet", strlen("packet")),
        RD_KAFKA_V_VALUE( (void*)msgStr.c_str(), msgStr.length() ),
        RD_KAFKA_V_END
    );
    //rd_kafka_flush(kafka_producer, 50);
}

std::string byte2hex(uint8 b) {
    static char table[] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
    std::string rval;
    rval.push_back( table[(b & 0xF0) >> 4] );
    rval.push_back( table[b & 0x0F] );
    return rval;
}
std::string str2hex(char* buff, int size) {
    std::string debugStr;
    for(uint32 i = 0; i < size; i++) {
        debugStr.append( byte2hex(buff[i]) );
    }
    return debugStr;
}

json to_json(socket_data socket) {
    json j;
    j["client_addr"] = ip2str(socket.client_addr);
    j["client_port"] = socket.client_port;
    return j;
}

json to_json(login_session_data_t session) {
    json j;
    j["accid"] = session.accid;
    j["login"] = session.login;
    return j;
}

void log_connect(socket_data socket, const char* state) {
    json msg;
    msg["socket"] = to_json(socket); 
    auto session = static_cast<login_session_data_t*>(socket.session_data);
    if (session != NULL) {
        msg["session"] = to_json(*session);
    }
    msg["state"] = state;
    msg["id"] = msg_id;
    msg_id += 1;
    std::string msgStr = msg.dump();
    rd_kafka_producev(kafka_producer,
        RD_KAFKA_V_TOPIC("lobby-socket"),
        RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
        RD_KAFKA_V_KEY( (void*)"msg", strlen("msg")),
        RD_KAFKA_V_VALUE( (void*)msgStr.c_str(), msgStr.length() ),
        RD_KAFKA_V_END
    );
    //rd_kafka_flush(kafka_producer, 50);
}

void log_packet(const char* topic, socket_data socket, std::string data) {
    json msg;
    msg["socket"] = to_json(socket);
    auto session = static_cast<login_session_data_t*>(socket.session_data);
    if (session != NULL) {
        msg["session"] = to_json(*session);
    }
    msg["data"] = base64_encode( (unsigned char*)data.c_str(), data.length() );
    msg["id"] = msg_id;
    msg_id += 1;
    std::string msgStr = msg.dump();
    rd_kafka_producev(kafka_producer,
        RD_KAFKA_V_TOPIC(topic),
        RD_KAFKA_V_MSGFLAGS(RD_KAFKA_MSG_F_COPY),
        RD_KAFKA_V_KEY( (void*)"msg", strlen("msg")),
        RD_KAFKA_V_VALUE( (void*)msgStr.c_str(), msgStr.length() ),
        RD_KAFKA_V_END
    );
    //rd_kafka_flush(kafka_producer, 50);
}