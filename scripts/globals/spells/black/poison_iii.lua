-----------------------------------
-- Spell: Poison
-----------------------------------
require("scripts/globals/magic")
require("scripts/globals/msg")
require("scripts/globals/status")
-----------------------------------
local spell_object = {}

spell_object.onMagicCastingCheck = function(caster, target, spell)
    return 0
end

spell_object.onSpellCast = function(caster, target, spell)
    local dINT = caster:getStat(xi.mod.INT) - target:getStat(xi.mod.INT)

    local power = math.min(caster:getSkillLevel(xi.skill.ENFEEBLING_MAGIC) / 15 + 1, 25)
    power = calculatePotency(power, spell:getSkillType(), caster, target)

    local duration = calculateDuration(180, spell:getSkillType(), spell:getSpellGroup(), caster, target)

    local params = {}
    params.diff = dINT
    params.skillType = xi.skill.ENFEEBLING_MAGIC
    params.bonus = 0
    params.effect = xi.effect.POISON
    local resist = applyResistanceEffect(caster, target, spell, params)

    if resist >= 0.5 then -- effect taken
        local resduration = duration * resist

        resduration = calculateBuildDuration(target, duration, params.effect)

        if resduration == 0 then
            spell:setMsg(xi.msg.basic.NONE)
        elseif target:addStatusEffect(params.effect, power, 3, resduration) then
            spell:setMsg(xi.msg.basic.MAGIC_ENFEEB_IS)
        else
            spell:setMsg(xi.msg.basic.MAGIC_NO_EFFECT)
        end
    else -- resist entirely.
        spell:setMsg(xi.msg.basic.MAGIC_RESIST)
    end

    return params.effect
end

return spell_object
