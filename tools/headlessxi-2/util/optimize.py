
import mysql.connector
import collections

class ModValues(object):
    def no_range(vals):
        for mod in ["RATT","RACC","RATTP"]:
            vals[mod] = 0

    def no_pdps(vals):
        for mod in ["STR","DEX","ATT","ACC","ATTP","DPS"]:
            vals[mod] = 0

    def no_mp(vals):
        for mod in ["MP", "MPP", "CONVHPTOMP"]:
            vals[mod] = 0

    def no_mdps(vals):
        for mod in ["INT","MATT","MACC"]:
            vals[mod] = 0

    def safe_from_pdps(vals):
        vals["CONVHPTOMP"] = 2
        for mod in ["DEF","DEFP","VIT","AGI","EVA"]:
            vals[mod] /= 2

    def tank(vals):
        vals["ENMITY"] = 10
        vals["CONVMPTOHP"] = 1
        for mod in ["VIT", "AGI", "DEFP", "DEF", "HP", "HPP"]:
            vals[mod] *= 2
        vals["MND"] /= 2

    def WAR(party=None):
        vs = dict(ModValues.base_values)
        vs["EVA"] /= 1.5
        ModValues.no_mp(vs)
        ModValues.no_mdps(vs)
        ModValues.no_range(vs)
        if party:
            ModValues.tank(vs)
        return vs

    def MNK(party=None):
        vs = dict(ModValues.base_values)
        vs["STR"] *= 1.5
        ModValues.no_mp(vs)
        ModValues.no_mdps(vs)
        ModValues.no_range(vs)
        return vs

    def WHM(party=None):
        vs = dict(ModValues.base_values)
        ModValues.no_range(vs)
        ModValues.no_mdps(vs)
        if party:
            ModValues.no_pdps(vs)
            ModValues.safe_from_pdps(vs)
        return vs

    def BLM(party=None):
        vs = dict(ModValues.base_values)
        ModValues.no_range(vs)
        if party:
            ModValues.no_pdps(vs)
            ModValues.safe_from_pdps(vs)
        return vs

    def RDM(party=None):
        vs = dict(ModValues.base_values)
        ModValues.no_range(vs)
        return vs
        
    def THF(party=None):
        vs = dict(ModValues.base_values)
        vs["DEX"] *= 1.5
        ModValues.no_mp(vs)
        ModValues.no_mdps(vs)
        return vs

    base_values = {
        "DEF":5, "HP":1, "HPP":5, "CONVMPTOHP":0, "MP":2, "MPP":10, "CONVHPTOMP":0,
        "STR":20, "DEX":20, "VIT":20, "AGI":20, "INT":20, "MND":20, "CHR":0,
        "ATT":5, "RATT":0, "ACC":5, "RACC":5, "ENMITY":0, "MATT":5, "MDEF":5,
        "MACC":5, "MEVA":5, "ATTP":5, "DEFP":5, "RATTP":5, "EVA":5, "DPS":10
    }

job_id_to_name = {
    1:"WAR", 2:"MNK", 3:"WHM", 4:"BLM", 5:"RDM", 6:"THF", 7:"PLD", 8:"DRK",
    9:"BST", 10:"BRD", 11:"RNG", 12:"SAM", 13:"NIN", 14:"DRG", 15:"SMN", 16:"BLU",
    17:"COR", 18:"PUP", 19:"DNC", 20:"SCH", 21:"GEO", 22:"RUN"
}

mod_id_to_name = {
    1:"DEF", 2:"HP", 3:"HPP", 4:"CONVMPTOHP", 
    5:"MP", 6:"MPP", 7:"CONVHPTOMP", 
    8:"STR", 9:"DEX", 10:"VIT", 11:"AGI", 12:"INT", 13:"MND", 14:"CHR",
    23:"ATT", 24:"RATT", 25:"ACC", 26:"RACC", 
    27:"ENMITY",
    28:"MATT", 29:"MDEF", 30:"MACC", 31:"MEVA",
    62:"ATTP", 63:"DEFP", 66:"RATTP", 68:"EVA"
}

skill_id_to_name = {
    1:"HAND_TO_HAND", 2:"DAGGER", 3:"SWORD", 4:"GREAT_SWORD", 5:"AXE", 6:"GREAT_AXE",
    7:"SCYTHE", 8:"POLEARM", 9:"KATANA", 10:"GREAT_KATANA", 11:"CLUB", 12:"STAFF"
}

class GearOptimize(object):
    def __init__(self, himi):
        self.himi = himi

    def decode_slots(self, slots):
        result = set()
        current = 0
        while slots > 0:
            if slots % 2 != 0:
                result.add(current)
            slots = slots >> 1
            current += 1
        return result

    def compute_value(self, mod_values, eq_id, job):
        value = 0
        eq = self.himi.eq_infos[eq_id]
        for mod in self.himi.eq_mods[eq_id]:
            if mod[0] not in mod_id_to_name:
                continue
            mod_name = mod_id_to_name[mod[0]]
            value += mod_values[mod_name] * mod[1]
        if eq["weapon"] is True:
            value += eq["DPS"] * mod_values["DPS"] * self.himi.skill_ranks[(job,eq["skill"])]
        return value

    exclude_eq = ["judges_cuirass", "judges_cuisses", "judges_gauntlets", 
        "judges_helm", "judges_ring", "judges_belt", 
        "judges_cape", "judges_shield", "judges_gorget", "judges_greaves", "fortune_egg", "happy_egg"]

    def optimize(self, gear, lvl, job, mod_values=None):
        best = {}
        if mod_values is None:
            mod_values = getattr(ModValues, job_id_to_name[job])(party=False)
        for eq_id in gear:
            eq = self.himi.eq_infos.get(eq_id, None)
            if eq is None:
                continue
            if eq["name"] in self.exclude_eq:
                continue
            if eq["slot"] == 3: # TODO: dual wielding
                eq["slots"] = [0]
            else:
                eq["slots"] = self.decode_slots(eq["slot"])
            if eq["level"] <= lvl and eq["jobs"] & (1 << (job-1)) != 0:
                eq["v"] = self.compute_value(mod_values, eq_id, job)
                if eq["v"] < 2:
                    continue
                bumped_eq = []
                for slot_id in eq["slots"]:
                    if eq.get("assigned", False) is True:
                        continue
                    for beq in bumped_eq:
                        if slot_id not in best:
                            best[slot_id] = beq
                        elif beq["v"] > best[slot_id]["v"]:
                            bumped_eq.append( best[slot_id] )
                            best[slot_id] = beq
                    bumped_eq = []
                    if slot_id not in best:
                        best[slot_id] = eq
                        eq["assigned"] = True
                    elif eq["v"] > best[slot_id]["v"]:
                        bumped_eq.append( best[slot_id] )
                        best[slot_id]["assigned"] = False
                        best[slot_id] = eq
                        eq["assigned"] = True
        return best 