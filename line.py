# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import datetime
from sql import Cast
from sql.operators import Concat

from trytond import backend
from trytond.model import ModelView, fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction

__all__ = ['Line']
__metaclass__ = PoolMeta


class Line:
    __name__ = 'timesheet.line'

    start = fields.DateTime('Start', states={
            'readonly': Bool(Eval('hours')),
            })
    end = fields.DateTime('End', states={
            'readonly': Bool(Eval('hours')),
            })

    @classmethod
    def __setup__(cls):
        super(Line, cls).__setup__()
        cls._buttons.update({
                'finish': {
                    'invisible': Eval('end')
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().cursor
        sql_table = cls.__table__()

        # Migration from 3.0: change start/end field type
        table = TableHandler(cursor, cls, module_name)
        migrate_start_end = False
        if table._columns['start']['typname'] == 'time':
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
            table = TableHandler(cursor, cls, module_name)
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
    def default_hours():
        return 0.0

    @staticmethod
    def default_start():
        return datetime.datetime.now()

    @fields.depends('start', 'end')
    def on_change_end(self):
        if self.start and self.end:
            return {
                'hours': self._calc_hours(self.end, self.start),
                }
        return {}

    @classmethod
    @ModelView.button
    def finish(cls, lines):
        for line in lines:
            line.stop()

    def stop(self):
        self.end = datetime.datetime.now()
        self.hours = self._calc_hours(self.end)
        self.save()

    def _calc_hours(self, end, start=None):
        if not start:
            start = self.start
        return round((end - start).seconds / 3600.0, 2)

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['start'] = cls.default_start()
        default['end'] = None
        default['hours'] = cls.default_hours()
        return super(Line, cls).copy(lines, default=default)
