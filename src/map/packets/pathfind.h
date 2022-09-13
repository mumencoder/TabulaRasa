
#ifndef _PATHFINDPACKET_H
#define _PATHFINDPACKET_H

#include "common/cbasetypes.h"
#include "../ai/helpers/pathfind.h"

#include "basic.h"

class CPathFind;

class CPathResultPacket : public CBasicPacket
{
public:
    CPathResultPacket(CPathFind&);
};

#endif