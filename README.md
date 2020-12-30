# UnConfig - a relaxed configuration framework for Python

Your Python application has configurable behavior; you want it to behave like
many Unix programs, where configuration values can be set with:

* command-line switches
* environment variables with a prefix
* configuration files: a global one under `/etc/` and local ones under
  `~/.config` (or perhaps specified by the user)

Doing this normally requires a fair bit of faffing about, when it ought to be
as simple as declaring what you want and getting on with the problem you're
trying to solve.

**UnConfig** aims to solve this for you by offering a simple declarative
syntax that by default allows all options to be set and overridden in order:

1. global config file values are overridden by
2. local config file values are overridden by
3. user-specified config file values are overridden by
4. environment variables are overridden by
5. command-line switches

While being able to explicitly alter default behavior.

```python
import validators
from unconfig import UnConfig, UnConfigItem

def url_helper(value):
	# This helper will validate whether a Valid URL is provided
	if validators.url(value):
		return value
	else:
		raise ValueError(f"{value} is not a URL")

# define your configuration
class MyConfig(UnConfig):
	verbose_level = UnConfigItem(default=0, long='verbose', short='v',
								 helper=int,
								 help="Verbosity level, takes an integer")
	url = UnConfigItem(help="URL to print", helper=url_helper)

# tell your object where to find config data
config = MyConfig(container='myapp', configfile='myapp.conf', env_prefix="myapp_")
config.load() # does it all! Processes config files, env vars, and command options

if config.verbose_level == 1:
	print("Being verbose")

print(config.url)

```

This produces a command-line app that will:

1. read `/etc/myapp/myapp.conf` for values, if it exists
2. read `$HOME/.config/myapp/myapp.conf` for values, if it exists
3. look for env variables named `myapp_url` and `myapp_verbose`, loading
   config values from them
4. parse the command line for `--verbose <num>` or `-v <num>` for verbosity
   and `--url <string>` for a URL

If run with `--help`, it will print a help document.

If run with `--configfile <config_file>`, it will read configuration from that file instead of
using steps 1 and 2 above.