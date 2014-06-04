# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .work import *
from .line import *


def register():
    Pool.register(
        Work,
        Line,
        Employee,
        StartWorkChooseAction,
        module='timetracker', type_='model')
    Pool.register(
        StartWork,
        module='timetracker', type_='wizard')

