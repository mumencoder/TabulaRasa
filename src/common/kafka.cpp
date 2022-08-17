
#include "kafka.h"

rd_kafka_t* kafka_producer;
rd_kafka_conf_t* kafka_conf;

void kafka_init() {
    char errstr[256];
    kafka_conf = rd_kafka_conf_new();
    rd_kafka_conf_set(kafka_conf, "bootstrap.servers", "broker:9092", errstr, sizeof(errstr));
    kafka_producer = rd_kafka_new(RD_KAFKA_PRODUCER, kafka_conf, errstr, sizeof(errstr));
}