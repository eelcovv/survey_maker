# -*- coding: utf-8 -*-
import logging

from pkg_resources import get_distribution, DistributionNotFound

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

console_format = '%(levelname)-8s [%(filename)s:%(lineno)4d] %(message)s'
logging.basicConfig(format=console_format, level=logging.WARNING)
