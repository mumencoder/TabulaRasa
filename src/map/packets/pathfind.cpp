
#include "../ai/helpers/pathfind.h"
#include "pathfind.h"

CPathResultPacket::CPathResultPacket(CPathFind& path) {
    this->setType(0x182);
    this->setSize(0x42);

    auto points = path.GetPathPoints();

    ref<uint16>(0x04) = points.size();
    int offset = 0x06;
    for(auto i = 0; i < 5 && i < points.size(); i++) {
        ref<float>(offset) = points[i].x;
        ref<float>(offset+4) = points[i].y;
        ref<float>(offset+8) = points[i].z;
        offset += 12;
    }    
}
