# isort:skip_file

import sys

from .metadata import get_package_version
from .logger import get_logger


__version__ = get_package_version(path=__file__, package_name='sdsstools')

NAME = 'sdsstools'


# Get a logger, mostly for the nice colouring.
log = get_logger(NAME)


from .configuration import *
from .logger import *
from .metadata import *
from ._vendor import color_print, releases, toml

# This is a hack to allow doing from sdsstools.color_print import color_text
# which some code already does.
sys.modules['sdsstools.color_print'] = color_print

# Allow to access releases as sdsstools.releases. This is important to
# define it as an extension in Sphinx.
sys.modules['sdsstools.releases'] = releases
