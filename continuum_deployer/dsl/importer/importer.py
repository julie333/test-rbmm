import click

from continuum_deployer.resources.deployment import DeploymentEntity


class Importer:
    """Interface that defines interaction with several DSL specific extractor implementations."""

    def __init__(self):
        self.app_modules = []

    def parse(self, dsl_input):
        """Handles actual parsing of DSL to internal data structures. Needs to be implemented by child."""
        raise NotImplementedError

    def get_app_modules(self):
        """Getter method for application modules"""
        return self.app_modules

    def print_app_modules(self):
        """Convenience helper that prints object representation of application modules"""
        click.echo(click.style("List of Deployments extracted:", fg='blue'))
        for module in self.app_modules:
            click.echo(str(module))