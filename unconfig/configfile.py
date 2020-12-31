"""
Parsing of config file in to key-value pairs for consumption
by UnConfig object
"""
import re
import logging
mlog = logging.getLogger(__name__)

def parse_config_file(filepath, separators=None, encoding='utf8', **kwargs):
	if separators is None:
		separators = [' ', ':', '=']

	line_re = re.compile(f'^\\s*(.+?)\\s*[{"".join(separators)}]\\s*(.+)$')

	config = {}
	with open(filepath, 'r', encoding=encoding, **kwargs) as configfile:
		for line in configfile.readlines():
			line = line.strip()
			if line.startswith('#') or len(line) == 0:
				# it's a comment, skip it
				mlog.debug("Skipping line '" + line + "'")
				continue

			result = line_re.match(line)
			if not result:
				raise ValueError(f"line '{line}' isn't valid")
			config[result.group(1)] = result.group(2)
			mlog.debug(f"Added: '{result.group(1)}' = '{result.group(2)}'")

	return config