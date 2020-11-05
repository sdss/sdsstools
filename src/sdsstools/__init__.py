# isort:skip_file

import sys

from .metadata import get_package_version


__version__ = get_package_version(path=__file__, package_name='sdsstools')

NAME = 'sdsstools'


from .configuration import *
from .logger import *
from .metadata import *
from ._vendor import color_print, toml

# This is a hack to allow doing from sdsstools.color_print import color_text
# which some code already does.
sys.modules['sdsstools.color_print'] = color_print
