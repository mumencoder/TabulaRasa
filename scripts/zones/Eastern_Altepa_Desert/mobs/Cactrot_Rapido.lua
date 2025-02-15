-----------------------------------
-- Area: Eastern Altepa Desert
-- NM  : Cactrot Rapido
-----------------------------------
require("scripts/globals/pathfind")
require("scripts/globals/titles")
-----------------------------------
local entity = {}

-- TODO: Set proper walking animation on engage

local pathNodes =
{
    -- x, y, z,
    -45, 0, -204,
    -99, 0, -179,
    -100, -1, -179,
    -103, -2, -178,
    -105, -3, -178,
    -110, -4, -177,
    -111, -5, -177,
    -116, -4, -176,
    -120, -3, -173,
    -122, -2, -171,
    -127, 0, -166,
    -136, 3, -153,
    -138, 3, -149,
    -140, 4, -142,
    -141, 4, -140,
    -141, 5, -138,
    -143, 5, -117,
    -144, 3, -110,
    -144, 2, -109,
    -144, 1, -107,
    -144, 0, -106,
    -144, 0, -105,
    -143, -1, -103,
    -142, -2, -102,
    -141, -1, -99,
    -140, 0, -96,
    -136, 1, -89,
    -133, 2, -83,
    -129, 1, -75,
    -126, 0, -69,
    -109, 0, -33,
    -104, -2, -24,
    -101, -3, -18,
    -97, -5, -11,
    -94, -7, -6,
    -87, -8,  8,
    -82, -10, 17,
    -78, -12, 24,
    -74, -13, 25,
    -69, -12, 25,
    -50, -13, 23,
    -44, -12, 22,
    -23, -12, 21,
    -18, -11, 20,
    -15, -11, 20,
    -10, -11, 20,
    -5, -11, 20,
    -2, -11, 20,
    1,  -11, 20,
    8,  -12, 19,
    12, -13, 18,
    16, -15, 17,
    20, -16, 16,
    23, -17, 16,
    25, -16, 15,
    27, -14, 15,
    29, -13, 15,
    32, -11, 14,
    35, -10, 13,
    38, -9,  12,
    45, -8,  10,
    59, -7,  5,
    92, -7, -9,
    95, -8, -12,
    102, -8, -16,
    105, -9, -19,
    106, -9, -20,
    107, -10, -21,
    110, -11, -23,
    112, -11, -25,
    116, -10, -28,
    116, -9, -29,
    123, -8, -39,
    124, -7, -41,
    130, -7, -61,
    129, -8, -66,
    120, -8, -80,
    119, -8, -81,
    114, -7, -83,
    100, -7, -87,
    78, -9, -92,
    74, -9, -96,
    72, -10, -100,
    65, -12, -110,
    57, -12, -123,
    54, -11, -129,
    51, -12, -133,
    47, -13, -138,
    45, -14, -140,
    45, -13, -142,
    43, -12, -144,
    42, -11, -146,
    36, -8, -154,
    33, -7, -159,
    28, -7, -167,
    22, -4, -177,
    20, -3, -180,
    19, -3, -182,
    14, -2, -183,
    13, -1, -184,
    -5, -1, -188,
    -10, 0, -189,
    -21, 0, -194,
    -29, 0, -198,
    -40, 0, -203,
}

entity.onPath = function(mob)
    xi.path.patrol(mob, pathNodes, xi.path.flag.RUN)
end

entity.onMobSpawn = function(mob)
    mob:setSpeed(250)
    entity.onPath(mob)
end

entity.onMobFight = function(mob)
    -- Speed and animsub are being ignored on engage, set here to ensure speed and animsub are set correctly
    if mob:getSpeed() > 40 or mob:getAnimationSub() > 0 then
        mob:setSpeed(40)
        mob:setAnimationSub(0)
    end
end

entity.onMobDisengage = function(mob)
    mob:setSpeed(250)
    mob:setAnimationSub(5)
end

entity.onMobRoam = function(mob)
    -- move to nearest path if not moving
    if not mob:isFollowingPath() then
        xi.path.pathToNearest(mob, pathNodes)
    end
end

entity.onMobDeath = function(mob, player, isKiller)
    player:addTitle(xi.title.CACTROT_DESACELERADOR)
end

entity.onMobDespawn = function(mob)
    UpdateNMSpawnPoint(mob:getID())
    mob:setRespawnTime(math.random(172800, 259200)) -- 2 to 3 days
end

return entity
