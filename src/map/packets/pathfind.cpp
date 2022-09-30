
#include "../ai/helpers/pathfind.h"
#include "pathfind.h"

CPathResultPacket::CPathResultPacket(CPathFind& path) {
    this->setType(0x182);
    this->setSize(0x42);

    auto points = path.GetPathPoints();
    int pts = std::min( 5, (int)points.size() );

    ref<uint16>(0x04) = pts;
    int offset = 0x06;
    for(auto i = 0; i < pts; i++) {
        ref<float>(offset) = points[i].position.x;
        ref<float>(offset+4) = points[i].position.y;
        ref<float>(offset+8) = points[i].position.z;
        offset += 12;
    }    
}
