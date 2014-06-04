# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime

from trytond.model import ModelView, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool

__all__ = ['Line']
__metaclass__ = PoolMeta


class Line:
    __name__ = 'timesheet.line'

    start = fields.Time('Start', states={'readonly': Bool(Eval('hours'))})
    end = fields.Time('End', states={'readonly': Bool(Eval('hours'))})

    @classmethod
    def __setup__(cls):
        super(Line, cls).__setup__()
        cls._buttons.update({
                'finish': {
                    'invisible': Eval('end')
                    },
                })

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['start'] = cls.default_start()
        default['end'] = None
        default['hours'] = cls.default_hours()

        return super(Line, cls).copy(lines, default=default)

    @classmethod
    @ModelView.button
    def finish(cls, lines):
        for line in lines:
            line.stop()

    @staticmethod
    def default_start():
        return datetime.datetime.now().time()

    @fields.depends('start', 'end')
    def on_change_end(self):
        if self.start and self.end:
            return {'hours': self._calc_hours(self.end, self.start)}
        return {}

    @staticmethod
    def default_hours():
        return 0.0

    def _calc_hours(self, end, start=None):
        today = datetime.datetime.today()
        end = datetime.datetime.combine(today, end)
        start = datetime.datetime.combine(today, start or self.start)
        return round((end - start).seconds / 3600.0, 2)

    def stop(self):
        self.end = datetime.datetime.now().time()
        self.hours = self._calc_hours(self.end)
        self.save()
