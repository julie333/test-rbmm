import copy
import sys

IDENTITY = 0x23420509
# dep_rules: deployment rules {a.factor: (f.factor, op, value)} (special value: IDENTITY):
# acc_rules: None (for combinatorial search), or {a.factor: op} for recursive search
# app = [Artefact({"vulnerability": 0.8, "memory": 200}), Artefact()]
# res = [Resource({"location": "intranet"}), Resource({"memory": 800, "location": "dmz"})]
# dep_rules = {
#     "vulnerability": ("location", "=", "dmz"),
#     "memory": ("memory", ">=", mm.IDENTITY),
#     "runtime": ("runtime", "=", mm.IDENTITY)
#
# print("---")
# print("Combinatorial mapping...")
# app = [Artefact({"vulnerability": 0.8, "memory": 200}), Artefact()]
# res = [Resource({"location": "intranet"}), Resource({"memory": 800, "location": "dmz"})]
# mapping = m.match(app, res, dep_rules, None)
#
# print("---")
# print("Recursive mapping... needs tree search!")
# app = [Artefact({"memory": 400}), Artefact({"memory": 800})]
# res = [Resource({"memory": 900}), Resource({"memory": 500})]
# mapping = m.match(app, res, dep_rules, acc_rules)

class Matchmaker:

    def match(self, app, res, dep_rules, acc_rules, level=0):
        print("/// enter mapping", app, "X", res, "@", level)
        mapping = {}
        if acc_rules:
            rescopy = copy.deepcopy(res)
            res = rescopy
        breakres = False
        for a in app:
            if breakres:
                break
            for r in res:
                # res = [Resource({"location": "intranet"}), Resource({"memory": 800, "location": "dmz"})]
                print("match", a, "X", r)
                if acc_rules:
                    rforig = copy.deepcopy(r.factors)
                valid = True
                if a.factors:
                    # app = [Artefact({"vulnerability": 0.8, "memory": 200}), Artefact()]
                    for f in a.factors:
                        print(" -", f)
                        if f in dep_rules:
                            # dep_rules = {
                            #     "vulnerability": ("location", "=", "dmz"),
                            #     "memory": ("memory", ">=", mm.IDENTITY),
                            #     "runtime": ("runtime", "=", mm.IDENTITY)
                            reval = False
                            rf, op, val = dep_rules[f]
                            if not r.factors or not rf in r.factors:
                                print("   !! factor absent from resource")
                            else:
                                rfval = r.factors[rf]
                                if val == IDENTITY:
                                    val = a.factors[f]
                                reval = self.matchop(rfval, op, val)
                            print("   ->", self.printablerules(dep_rules[f]), reval)
                            if not reval:
                                valid = False
                        if acc_rules and valid:
                            if f in acc_rules:
                                if f in r.factors and f in a.factors:
                                    op = acc_rules[f]
                                    if op == "-":
                                        print("# reduce", f, "in", r, "by", a.factors[f])
                                        r.factors[f] -= a.factors[f]
                                else:
                                    print("!! factor absent in resource or app")
                print("= valid", valid)
                if valid:
                    mapping[a] = r
                    if not acc_rules:
                        break
                    else:
                        print("//> partial mapping", a, "->", r)
                        # recursion starts here
                        remres = []
                        for rr in res:
                            if r != rr:
                                remres.append(rr)
                        remapp = []
                        for ra in app:
                            if a != ra:
                                remapp.append(ra)
                        if remapp:
                            # shortcut, not strictly necessary
                            rmapping = self.match(remapp, remres, dep_rules, acc_rules, level + 1)
                            if not rmapping:
                                valid = False
                            else:
                                for a in rmapping:
                                    mapping[a] = rmapping[a]
                        if valid:
                            breakres = True
                            break
                if not valid:
                    if acc_rules:
                        r.factors = rforig
            if not a in mapping:
                print("!! mapping failed")
                return

        print("/// leave mapping:", mapping, "@", level)
        return mapping

    def printablerules(self, r):
        rx = r[2]
        if rx == IDENTITY:
            rx = "*"
        return f"({r[0]} {r[1]} {rx})"

    def matchop(self, rfval, op, val):
        r = False
        if op == "=":
            if rfval == val:
                r = True
        elif op == ">=":
            if rfval >= val:
                r = True
        elif op == "<=":
            if rfval <= val:
                r = True
        elif op == "<>" or op == "!=":
            if rfval != val:
                r = True
        return r