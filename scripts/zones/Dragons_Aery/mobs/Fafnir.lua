-----------------------------------
-- Area: Dragons Aery
--  HNM: Fafnir
-----------------------------------
local ID = require("scripts/zones/Dragons_Aery/IDs")
mixins = {require("scripts/mixins/rage")}
require("scripts/globals/settings")
require("scripts/globals/status")
require("scripts/globals/titles")
-----------------------------------
local entity = {}

entity.onMobSpawn = function(mob)
    mob:setMobMod(xi.mobMod.DRAW_IN, 1)
    mob:setMobMod(xi.mobMod.DRAW_IN_CUSTOM_RANGE, 20)
    mob:setMobMod(xi.mobMod.DRAW_IN_FRONT, 1)

    if xi.settings.main.LandKingSystem_NQ > 0 or xi.settings.main.LandKingSystem_HQ > 0 then
        GetNPCByID(ID.npc.FAFNIR_QM):setStatus(xi.status.DISAPPEAR)
        SetDropRate(918, 1526, 0) -- do not drop wyrm beard
        mob:setMobMod(xi.mobMod.IDLE_DESPAWN, 180)
    end
    if xi.settings.main.LandKingSystem_HQ == 0 then
        SetDropRate(918, 3340, 0) -- do not drop cup_of_sweet_tea
    end

    mob:setLocalVar("[rage]timer", 3600) -- 60 minutes
end

entity.onMobDeath = function(mob, player, isKiller)
    player:addTitle(xi.title.FAFNIR_SLAYER)
end

entity.onMobDespawn = function(mob)
    local timeOfDeath = GetServerVariable("[POP]Nidhogg")
    local kills       = GetServerVariable("[PH]Nidhogg")
    local popNow      = math.random(1, 5) == 3 or kills > 6

    if xi.settings.main.LandKingSystem_HQ ~= 1 and timeOfDeath <= os.time() and popNow then
        -- 0 = timed spawn, 1 = force pop only, 2 = BOTH
        if xi.settings.main.LandKingSystem_NQ == 0 then
            DisallowRespawn(ID.mob.FAFNIR, true)
        end

        DisallowRespawn(ID.mob.NIDHOGG, false)
        UpdateNMSpawnPoint(ID.mob.NIDHOGG)
        GetMobByID(ID.mob.NIDHOGG):setRespawnTime(75600 + math.random(0, 6) * 1800) -- 21 - 24 hours with half hour windows
    else
        if xi.settings.main.LandKingSystem_NQ ~= 1 then
            UpdateNMSpawnPoint(ID.mob.FAFNIR)
            GetMobByID(ID.mob.FAFNIR):setRespawnTime(75600 + math.random(0, 6) * 1800) -- 21 - 24 hours with half hour windows
            SetServerVariable("[PH]Nidhogg", kills + 1)
        end
    end
    -- Respawn the ???
    if xi.settings.main.LandKingSystem_HQ == 2 or xi.settings.main.LandKingSystem_NQ == 2 then
        GetNPCByID(ID.npc.FAFNIR_QM):updateNPCHideTime(xi.settings.main.FORCE_SPAWN_QM_RESET_TIME)
    end
end

return entity
