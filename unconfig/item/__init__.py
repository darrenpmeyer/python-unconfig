"""
Collection of Item classes
"""
import logging
mlog = logging.getLogger(__name__)


# TODO more-specific errors around validation failures so we can see which
# items failed in an except block


def default_filter(value):
	return value


class UnConfigItem(object):
	def __init__(
		self,
		default=None,  # default value for configuration item
		filter=None,  # call filter to validate/normalize value
		long=None,  # long option name (default: field name)
		short=None,  # short (1-character) option name
		help=None,  # help text for CLI/etc.
	):
		self._value = default  # NB: do not run filter on default value!
		self.default = default

		if filter is None:
			self.filter = default_filter
		elif not callable(filter):
			raise ValueError("Filter must be a callable item")
		else:
			self.filter = filter

		self.long = long
		self.short = short
		self.help = help

	def __str__(self):
		return str(self.value)

	def __int__(self):
		return int(self.value)

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, value):
		self._value = self.filter(value)
	


class UnConfigIncremeterItem(UnConfigItem):
	def __init__(self, *args, limit=None, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		self.limit = limit

	@UnConfigItem.value.setter
	def value(self, value):
		mlog.debug(f"Set incrementer value using argument '{value}'")
		new_value = value
		if new_value is None:
			new_value = self.filter(self._value + 1)
			mlog.debug(f"-> None acting as incrementer, will set {new_value}")
		
		if self.limit is not None and new_value > self.limit:
			# new value has exceeded the specified limit
			raise ValueError(f"New value {new_value} would exceed limit of {self.limit}")

		self._value = int(new_value)  # set only if limit wasn't exceeded