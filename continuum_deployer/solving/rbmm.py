import click
import copy
import sys

from continuum_deployer.resources.resource_entity import ResourceEntity
from continuum_deployer.solving.solver import Solver
from continuum_deployer.utils.config import Config, Setting, SettingValue

IDENTITY = 0x23420509


class MultiFactor:
    def __init__(self, f=None):
        self.factors = f

    def __str__(self):
        tn = type(self).__name__
        tn += "[" + str(self.factors) + "]"
        return tn

    def __repr__(self):
        return str(self)


class Resource(MultiFactor):
    pass


class Artefact(MultiFactor):
    pass


class Rbmm(Solver):

    @staticmethod
    def deploy_iterate(entity, resource):
        if resource.add_deployment(entity):
            return True
        return False

    def _gen_config(self):
        return Config([])

    def rbmm_match(self, entities, resources):
        app = []
        res = []
        resList = list(resources)
        entityList = list(entities)

        # DeploymentEntity -> Artefact, considering only cpu & memory for now but can be extended to add all props of Deployment entity
        for entity in entityList:
            app.append(Artefact({"name": entity.name, "cpu": entity.cpu, "memory": entity.memory}))

        # ResourceEntity -> Resource
        for r in resList:
            res.append(Resource({"name": r.name, "cpu": r.cpu, "memory": r.memory}))

        # Dep Rules
        dep_rules = {"memory": ("memory", ">=", IDENTITY),
                     "cpu": ("cpu", ">=", IDENTITY)}

        # Acc Rules
        # acc_rules = None
        acc_rules = {"memory": "-"}

        # map Artefacts ( i.e, Deployment entities) to resources
        mapping = Rbmm.mapArtefactResources(self, app, res, dep_rules, acc_rules, 0, None)

        newMappingDict = {}
        for k, v in mapping.items():
            newMappingDict[k.factors.get('name')] = v

        for entity in entities:
            # Get resource mapping of artefact of same name from entity
            mappedResource = newMappingDict.get(entity.name)

            # Resource -> ResourceEntity
            resEntity = next((x for x in resources if x.name == mappedResource.factors.get('name')), None)

            if not Rbmm.deploy_iterate(entity, resEntity):
                self.placement_errors.append(entity)

    def do_matching(self, deployment_entities, resources):
        self.rbmm_match(
            deployment_entities,
            resources
        )

    def mapArtefactResources(self, app, res, dep_rules, acc_rules, level=0, skip=None):
        print("/// enter mapping", app, "X", res, "@", level)
        if skip:
            a_copy = {}
            r_copy = {}
            for f in skip:
                for a in app:
                    if f in a.factors:
                        a_copy.setdefault(a, {})[f] = a.factors[f]
                        del a.factors[f]
                        print("! filter", a, f)
                for r in res:
                    if f in r.factors:
                        r_copy.setdefault(r, {})[f] = r.factors[f]
                        del r.factors[f]
                        print("! filter", r, f)
        mapping = {}
        if acc_rules:
            rescopy = copy.deepcopy(res)
            res = rescopy
        breakres = False
        for a in app:
            if breakres:
                break
            for r in res:
                print("match", a, "X", r)
                if acc_rules:
                    rforig = copy.deepcopy(r.factors)
                valid = True
                if a.factors:
                    for f in a.factors:
                        print(" -", f)
                        if f in dep_rules:
                            reval = False
                            rf, op, val = dep_rules[f]
                            if not r.factors or not rf in r.factors:
                                print("   !! factor absent from resource")
                            else:
                                rfval = r.factors[rf]  # take value from resource, eg node-1
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
                                        # reduce memory in Resource[{'name': 'node-3', 'cpu': 2, 'memory': 540}] by 536
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
                            rmapping = self.mapArtefactResources(remapp, remres, dep_rules, acc_rules, level + 1)
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
        if skip:
            for a in a_copy:
                a.factors.update(a_copy[a])
            for r in res:
                r.factors.update(r_copy[r])
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

    def match(self):
        super(Rbmm, self).match()
