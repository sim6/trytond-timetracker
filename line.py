# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from datetime import datetime, timedelta
from sql import Cast
from sql.operators import Concat

from trytond import backend
from trytond.model import ModelView, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Line']


class Line:
    __metaclass__ = PoolMeta
    __name__ = 'timesheet.line'
    start = fields.DateTime('Start')
    end = fields.DateTime('End')

    @classmethod
    def __setup__(cls):
        super(Line, cls).__setup__()
        cls._buttons.update({
                'finish': {
                    'invisible': ~Eval('start') | Eval('end')
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().connection.cursor()
        sql_table = cls.__table__()

        # Migration from 3.0: change start/end field type
        table = TableHandler(cls, module_name)
        migrate_start_end = False
        if (table.column_exist('start') and
                table._columns['start']['typname'] == 'time'):
            migrate_start_end = True

            def get_bak_column_name(column_name):
                column_bak = column_name + '_bak'
                bak_it = 0
                while table.column_exist(column_bak):
                    column_bak = column_name + '_bak%d' % bak_it
                    bak_it += 1
                return column_bak

            start_column_bak = get_bak_column_name('start')
            table.column_rename('start', start_column_bak, exception=True)

            end_column_bak = get_bak_column_name('end')
            table.column_rename('end', end_column_bak, exception=True)

        super(Line, cls).__register__(module_name)

        if migrate_start_end:
            table = TableHandler(cls, module_name)
            date_start_bak = Concat(Concat(sql_table.date, ' '),
                getattr(sql_table, start_column_bak))
            date_end_bak = Concat(Concat(sql_table.date, ' '),
                getattr(sql_table, end_column_bak))
            cursor.execute(*sql_table.update(
                    columns=[sql_table.start, sql_table.end],
                    values=[
                        Cast(date_start_bak, 'timestamp'),
                        Cast(date_end_bak, 'timestamp'),
                    ]))
            table.drop_column(start_column_bak, exception=True)
            table.drop_column(end_column_bak, exception=True)

    @staticmethod
    def default_start():
        return datetime.now()

    @staticmethod
    def default_duration():
        return timedelta(seconds=0)

    @fields.depends('start', 'duration')
    def on_change_duration(self):
        if self.start and self.duration is not None:
            self.end = self.start + self.duration

    @fields.depends('start', 'end')
    def on_change_start(self):
        if self.start and self.end:
            self.duration = self._calc_duration(self.end, self.start)

    @fields.depends('start', 'end')
    def on_change_end(self):
        if self.start and self.end:
            self.duration = self._calc_duration(self.end, self.start)

    @classmethod
    @ModelView.button
    def finish(cls, lines):
        for line in lines:
            line.stop()

    def stop(self):
        self.end = datetime.now()
        self.duration = self._calc_duration(self.end)
        self.save()

    def _calc_duration(self, end, start=None):
        if not start:
            start = self.start
        return end - start

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['start'] = cls.default_start()
        default['end'] = None
        default['duration'] = cls.default_duration()
        return super(Line, cls).copy(lines, default=default)
