
#include "map/entities/charentity.h"
#include "map/packets/basic.h"
#include "map/map.h"
#include "login/login_session.h"
#include <rdkafka.h>

void kafka_init();

void log_map_packet_in(map_session_data_t* const PSession, CCharEntity* const PChar, CBasicPacket data);
void log_map_packet_out(map_session_data_t* const PSession, CCharEntity* const PChar, CBasicPacket data);

void log_packet(const char* topic, socket_data socket, std::string data);
void log_connect(socket_data socket, const char* state);

#define LOG_READ_PACKET(topic, fd) log_packet(topic, *sessions[fd], sessions[fd]->rdata.substr(0, RFIFOREST(fd)))
#define LOG_WRITE_PACKET(topic, fd) log_packet(topic, *sessions[fd], sessions[fd]->wdata)
