"""
UnConfig - unix-style configuration made dead easy
"""
from pprint import pformat
import os
import sys
import warnings
import logging
mlog = logging.getLogger(__name__)

from .configfile import parse_config_file
# from .item import *
import unconfig.item


class UnConfig(object):
	def __init__(
		self,
		container=None,  # container (e.g. directory) name for the config
		configfile=None,  # config file name for the config
		config_search_path=None,  # path to search for configs in
		env_prefix=None,  # env var prefix
	):
		self.config_file_separators = [' ', ':', '=']  # can set to change config file format

		if container is None:
			self._container = ''
		else:
			self._container = container

		if configfile is None:
			raise ValueError("parameter 'configfile' is required")
		self._configfile = configfile

		self.configfile = unconfig.item.UnConfigItem(
			default=None,
			filter=str,
			help="Specify a configuration file to read")
		self.env_prefix = unconfig.item.UnConfigItem(
			default=env_prefix,
			filter=str,
			help=("Specify the environment variable prefix to read" + 
				  "configuration values from"))

		if config_search_path is None:
			self._config_search_path = [
				'/etc',
				os.path.join(os.getenv('HOME'), '.config'),
				os.path.abspath('.')  # TODO revisit this: am I sure I want curdir in here?
			]
		else:
			self._config_search_path = config_search_path

		self.setup()  # inheriting classes implement this to add arguments

		# now build long and short lookup tables
		self._longs = {}
		self._shorts = {}
		self._arguments = [name for name in self.__dict__.keys() if not name.startswith('_')]
		for field in self._arguments:
			mlog.debug(f"processing field '{field}'")
			item = self.__dict__[field]

			if not isinstance(item, unconfig.item.UnConfigItem):
	
				msg = (f"{field} does not descend from UnConfigItem; skipping")
				mlog.debug(msg)
				# warnings.warn(msg)
				continue  # move to the next field

			if item.long is None:
				# auto-create long if one isn't specified
				longname = field.replace('_', '-')  # option name should use - where field name has _
				item.long = longname
				mlog.debug(f"Auto-generated long option '{longname}' "
					       f"from '{field}'")

			self._longs[item.long] = item
			if item.short is not None:
				item.short = str(item.short)
				if len(item.short) != 1:
					raise ValueError("Short identifiers must be eactly one char")
				self._shorts[item.short] = item

		mlog.debug(f"Longs: {pformat(self._longs, 2)}")

	def setup(self):
		pass

	def show_help(self):
		progname = sys.argv[0]
		msg = f"Usage: {progname} [options]\n"  # TODO better usage string
		for name in self._longs:
			declarestr = f"  --{name}"
			if self._longs[name].short is not None:
				declarestr += f", -{self._longs[name].short}"
			msg += declarestr + "\n"
			if self._longs[name].help is not None and len(self._longs[name].help):
				msg += f"\t{self._longs[name].help}\n"  # TODO wrap help text
		
		print(msg, file=sys.stderr)


	def load_file(self, filename):
		mlog.info(f"Loading file '{filename}'")
		result = parse_config_file(filename)
		# mlog.debug(result)
		for name in result.keys():
			if name not in self._longs:
				raise ValueError(f"item '{name}' in '{filename}' doesn't map to a configuration item")
			self._longs[name].value = result[name]

	def load_env(self):
		mlog.warn("load_env not implemented yet")

	def load_argv(self, argv=None, filter=None):
		"""
		Parses command-line arguments and sets items appropriately

		Filter makes load_argv only look at a specific list of arguments
		"""
		if argv is None:
			argv = sys.argv[1:]  # don't include program name
		mlog.debug(f"Enter load_argv with {argv}")

		leftover_args = []

		i = 0
		while i < len(argv):
			mlog.debug(f"Considering {i:>2d}: '{argv[i]}'")
			current = i
			if argv[current].startswith('-'):
				# long option
				name = argv[current].replace('-','')
				argument = None

				try:
					mlog.debug(f"Possible arugment to {name}: '{argv[i+1]}'")
					if not argv[i+1].startswith('-'):
						# it's not the next switch!
						mlog.debug("looks like an argument!")
						argument = argv[i+1]
						i += 1  # skip the next arg, since it's not a switch
				except IndexError as e:
					# there isn't a next argv, so nothing to pass
					mlog.debug("Index exceeded in argv lookahead")

				if filter is not None and name not in filter:
					# skip, and add it to the leftover args
					mlog.debug(f"Skipping arg '{name}' because it's not in the filter")
					leftover_args.append(argv[current])
					if argument is not None:
						leftover_args.append(argument)
					i += 1
					continue

				if argv[current].startswith('--') and name in self._longs:
					mlog.debug(f"Set long '{name}' = {argument!r}")
					self._longs[name].value = argument
					mlog.debug(f"New value of '{name}' is {self._longs[name]}")
				elif len(name) == 1 and name in self._shorts:
					mlog.debug(f"Set short '{name}' = {argument!r}")
					self._shorts[name].value = argument
					mlog.debug(f"New value of '{name}' is {self._shorts[name]}")
				else:
					raise ValueError(f"Switch {argv[i]} isn't defined")

			else:
				mlog.debug(f"Couldn't make sense of '{argv[i]}', adding to leftovers")
				leftover_args.append(argv[i])
			i += 1

		return leftover_args

	def load(self, argv=None):
		if argv is None:
			argv = sys.argv[1:]  # don't include program name

		# Display help if aksed
		# TODO put this in a Item class so that implementors can specify a different word
		if '--help' in argv:
			return self.show_help()

		# look for the options that change file an env processing
		argv = self.load_argv(argv=argv, filter=['configfile', 'env_prefix'])
		mlog.debug(f"New argv: {argv}")

		# first load config files
		self._config_files = []
		if self.configfile.value is not None:
			# our user has provided a configuration file, load only that
			mlog.info(f"Loading only user specified config file '{self.configfile!s}'")
			self._config_files = [self.configfile.value]
		else:
			for path in self._config_search_path:
				path = os.path.join(path, self._container)
				if not os.path.isdir(path):
					mlog.info("No directory '{path}', skipping search")
					continue
				configfile = os.path.join(path, self._configfile)
				if not os.path.isfile(configfile):
					mlog.info(f"No file '{self._configfile}' in '{path}'")
					continue
				mlog.info(f"Adding file '{configfile}' to queue")
				self._config_files.append(configfile)

		for configfile in self._config_files:
			self.load_file(configfile) # TODO load multiple files by tree

		# now find overrides for 
		self.load_env()
		params = self.load_argv(argv=argv)  # params contains anything that wasn't part of an option

