-----------------------------------
-- Area: Yhoator Jungle
--  Mob: Tonberry Shadower
-- Note: PH for Hoar-knuckled Rimberry
-----------------------------------
local ID = require("scripts/zones/Yhoator_Jungle/IDs")
mixins = {require("scripts/mixins/families/tonberry")}
require("scripts/globals/regimes")
require("scripts/globals/mobs")
-----------------------------------
local entity = {}

entity.onMobDeath = function(mob, player, isKiller)
    xi.regime.checkRegime(player, mob, 133, 1, xi.regime.type.FIELDS)
end

entity.onMobDespawn = function(mob)
    xi.mob.phOnDespawn(mob, ID.mob.HOAR_KNUCKLED_RIMBERRY_PH, 10, 5400) -- 90 minute minimum
end

return entity
