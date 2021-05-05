from argparse import ArgumentParser
from collections import namedtuple
from pathlib import Path
import logging
from arcgis.gis import GIS
from .constants import *
from .restore import Restore
from .backup import Backup


class Environment(object):

    def process_args(self, argv):
        parser = ArgumentParser()

        if PORTAL in argv:
            parser.add_argument('-u', '--username', type=str, required=False, help='Portal username (case-sensitive)')
            parser.add_argument('-p', '--password', type=str, required=False, help='Portal password (case-sensitive)')
            parser.add_argument('-g', '--gis', type=str, required=True, help='Portal url')

        if LOGGER in argv:
            parser.add_argument('-o', '--output', type=str, required=False, help='Logger output path.')
            parser.add_argument('-v', '--verbose', action='store_true', required=False, help='Print all staged edits to console.')

        if CONFIGURATION in argv:
            parser.add_argument('-c', '--configuration', type=str, required=True, help='Perform script from configuration file.')

        if BACKUP in argv:
            parser.add_argument('-b', '--backup', type=str, required=False, help='Path to directory where backups will be written.')

        if RESTORE in argv:
            parser.add_argument('-r', '--restore', type=str, required=True, nargs='+', help='Paths to backups.')

        if DEV in argv:
            parser.add_argument('-d', '--dev', type=int, required=False, help='Run script in developer mode.')

        self.args = parser.parse_args()

    # Get Environment
    _portal = None
    _gis = None
    _data = None
    _logger = None
    def __getattr__(self, attr):
        if attr == PORTAL:
            if self._portal:
                return self._portal
            # First try args
            if self.args.username and self.args.password:
                self._portal = GIS(url=self.args.gis, username=self.args.username, password=self.args.password)
                return self._portal
            # Second try environment
            import os
            env_u = os.getenv('AFD_PORTAL_USERNAME')
            env_p = os.getenv('AFD_PORTAL_PASSWORD')
            if env_u and env_p:
                self._portal = GIS(url=self.args.gis, username=env_u, password=env_p)
                return self._portal
            # If no credentials are supplied, raise exception.
            raise Exception('You have not supplied Portal credentials.')

        elif attr == CONFIGURATION:
            Configuration = namedtuple('Configuration', 'gis yml')
            if self._gis is not None and self._data is not None:
                return Configuration(self._gis, self._data)
            import yaml
            if self.args.configuration:
                with open(self.args.configuration) as f:
                    self._data = yaml.load(f, Loader=yaml.FullLoader)
                    if 'portal' not in self._data:
                        raise Exception('The configuration file is not formatted properly.')
                    portal = self._data['portal']
                    if 'url' not in portal:
                        raise Exception('The configuration file is not formatted properly, missing portal url.')
                    # First try config file
                    if 'username' in portal and 'password' in portal:
                        self._gis = GIS(portal['url'], portal['username'], portal['password'])
                    # Second try environment
                    else:
                        import os
                        username = os.getenv('AFD_PORTAL_USERNAME')
                        password = os.getenv('AFD_PORTAL_PASSWORD')
                        self._gis = GIS(url=portal['url'], username=username, password=password)
                    # Finally, return results
                    if self._gis is not None and self._data is not None:
                        return Configuration(self._gis, self._data)
                    else:
                        raise Exception('The configuration file is not formatted properly, could not build GIS client.')
            else:
                raise Exception('You have not supplied a configuration file.')

        elif attr == LOGGER:
            if self._logger is not None:
                return self._logger
            # Build logger
            parser = ArgumentParser()
            logger = logging.getLogger(parser.prog)
            logger.setLevel(logging.DEBUG)
            # Build Console Handler
            console = logging.StreamHandler()
            console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            console.setFormatter(console_format)
            # If verbose, we want all messages logged to console.
            if self.args.verbose:
                console.setLevel(logging.DEBUG)
            # Otherwise, we want INFO and greater messages logged to console.
            else:
                console.setLevel(logging.INFO)
            logger.addHandler(console)
            # Build File Handler
            if self.args.output:
                file = logging.FileHandler(self.args.output)
                # We want all messages written to output log.
                file.setLevel(logging.DEBUG)
                file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file.setFormatter(file_format)
                logger.addHandler(file)

            self._logger = logger
            return logger

        elif attr == BACKUP:
            return Backup(self.args.backup)

        elif attr == RESTORE:
            return [Path(path) for path in self.args.restore]

        elif attr == DEV:
            if self.args.dev and self.args.dev > 0:
                return self.args.dev
            else:
                return None


ENV = Environment()


def args(*argv):
    def inner(function):
        def wrapper(*args, **kwargs):
            ENV.process_args(argv)
            # Perform decorated function.
            result = function(*args, **kwargs)
            return result
        return wrapper
    return inner
