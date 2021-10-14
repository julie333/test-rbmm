import click
import copy
import sys

from continuum_deployer.resources.resource_entity import ResourceEntity
from continuum_deployer.solving.solver import Solver
from continuum_deployer.utils.config import Config, Setting, SettingValue

IDENTITY = 0x23420509

class Rbmm(Solver):

    @staticmethod
    def deploy_iterate(entity, resources):
        """Helper that traverses a list of resources and tries to place the given
        deploment entity on one of the resources.

        :param entity: deployment entity that should be placed
        :type entity: :class:`continuum_deployer.resources.deployment.DeploymentEntity`
        :param resources: list of resource entities that are valid targets
        :type resources: list
        :return: boolean flag representing the success of the placement attempt
        :rtype: bool
        """
        for resource in resources:
            if resource.add_deployment(entity):
                return True
        return False

    def _gen_config(self):
        return Config([
            Setting('target', [
                SettingValue(
                    'cpu', description='Sorts resources and workloads by cpu for greedy matching', default=True),
                SettingValue(
                    'memory', 'Sorts resources and workloads by memory for greedy matching'),
            ])
        ])

    # def greedy_attr(self, entities, resources, attr):
    #     entities_sorted = Greedy.sort_by_attr(entities, attr)
    #     resources_sorted = Greedy.sort_by_attr(resources, attr)
    #
    #     for entity in entities_sorted:
    #         if not Greedy.deploy_iterate(entity, resources_sorted):
    #             self.placement_errors.append(entity)

    def do_matching(self, deployment_entities, resources):
        """Does actual deployment to resource matching"""

        # self.greedy_attr(
        #     deployment_entities,
        #     resources,
        #     self.config.get_setting('target').get_value().value
        # )

        app = [({"vulnerability": 0.8, "memory": 200, "runtime": "java"})];
        resources = [({"location": "intranet"}), ({"memory": 800, "location": "dmz"})]
        # dep_rules: deployment rules {a.factor: (f.factor, op, value)} (special value: IDENTITY)
        dep_rules = {
             "vulnerability": ("location", "=", "dmz"),
             "memory": ("memory", ">=", IDENTITY),
             "runtime": ("runtime", "=", IDENTITY)
        }

        self.rbmm_match(
            app,
            resources,
            dep_rules
        )

    def rbmm_match(self, app, res, dep_rules):
        print("/// enter mapping", app, "X", res)
        mapping = {}
        for a in app:
            for r in res:
                print("match", a, "X", r)
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
                                rfval = r.factors[rf]
                                if val == IDENTITY:
                                    val = a.factors[f]
                                reval = self.matchop(rfval, op, val)
                            print("   ->", self.printablerules(dep_rules[f]), reval)
                            if not reval:
                                valid = False
                print("= valid", valid)
                if valid:
                    mapping[a] = r
                    break

            if not a in mapping:
                print("!! mapping failed")
                return

        print("/// leave mapping:", mapping)
        return mapping

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

    def printablerules(self, r):
        rx = r[2]
        if rx == IDENTITY:
            rx = "*"
        return f"({r[0]} {r[1]} {rx})"
