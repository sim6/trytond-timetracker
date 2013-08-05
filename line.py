#This file is part of timetracker.The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, And, Equal
import datetime
import time
from decimal import Decimal


__metaclass__ = PoolMeta

__all__ = ['Line']


class Line:
    __name__ = 'timesheet.line'

    start = fields.Time('Start')
    end = fields.Time('End')

    def _calc_hours(self, end, start=None):
        today = datetime.datetime.today()
        end = datetime.datetime.combine(today, end)
        start = datetime.datetime.combine(today, start or self.start)
        return  round((end - start).seconds / 3600.0,2)

    def stop(self):
        self.end = datetime.datetime.now().time()
        self.hours = self._calc_hours(self.end)
        self.save()


