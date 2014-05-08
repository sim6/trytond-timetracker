#This file is part of timetracker.The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateTransition, StateView, Button
import datetime

__metaclass__ = PoolMeta

__all__ = ['Work', 'Employee', 'StartWorkStart', 'StartWork']


class Employee:
    __name__ = 'company.employee'

    def working_on(self):
        lines = self.opened_timesheet_lines()
        return [x.work for x in lines]

    def opened_timesheet_lines(self):
        Line = Pool().get('timesheet.line')
        lines = Line.search([('end', '=', None),
                ('employee', '=', self.id)])
        return lines


class StartWorkStart(ModelView):
    'Start Work Start'
    __name__ = "timesheet.line.start_work.start"

    opened_lines = fields.Many2Many('timesheet.line',
            None, None, 'Opened Lines', readonly=True)
    opened_tasks = fields.Many2Many('project.work',
            None, None, 'Opened Tasks', readonly=True)

    @staticmethod
    def default_opened_lines():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return [x.id for x in user.employee.opened_timesheet_lines()]

    @staticmethod
    def default_opened_tasks():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return [x.id for x in user.employee.working_on()]


class StartWork(Wizard):
    'Start Work'
    __name__ = 'timesheet.line.start_work'

    start = StateView('timesheet.line.start_work.start',
        'timetracker.start_work_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Discard & Start', 'discard_and_start_work'),
            Button('Close & Start', 'close_and_start_work', default=True)
            ])

    close_and_start_work = StateTransition()
    discard_and_start_work = StateTransition()

    def transition_close_and_start_work(self):
        Task = Pool().get('project.work')
        Task.stop_work(self.start.opened_tasks)
        task = Task(Transaction().context['active_id'])
        task.start_work()
        return 'end'

    def transition_discard_and_start_work(self):
        Task = Pool().get('project.work')
        Task.cancel_work(self.start.opened_tasks)
        task = Task(Transaction().context['active_id'])
        task.start_work()
        return 'end'


class Work:
    __name__ = 'project.work'

    working_employees = fields.Function(fields.Many2Many('company.employee',
            None, None, 'Emloyee Working',
            help='Employees working on this work'), 'get_working_employees')

    @classmethod
    def __setup__(cls):
        super(Work, cls).__setup__()
        cls._buttons.update({
                'start_work_wizard': {
                    'invisible': (Eval('type') == 'project')
                    },
                'stop_work': {
                    'invisible': (Eval('type') == 'project')
                        },
                'cancel_work': {
                    'invisible': (Eval('type') == 'project')
                    },
                })

    def get_working_employees(self, name=None):
        Line = Pool().get('timesheet.line')
        lines = Line.search([
                ('work', '=', self.id),
                ('end', '=', None)])
        if not lines:
            return []
        return [x.employee.id for x in lines]

    def get_open_timesheet_line(self):
        Line = Pool().get('timesheet.line')
        lines = Line.search([
                ('end', '=', None),
                ('employee', '=', self.id),
                ('work', '=', self.id),
                ])
        return [x.id for x in lines]

    def get_employee(self):
        User = Pool().get('res.user')
        user = User(Transaction().user)
        if user.employee:
            return user.employee.id
        else:
            return False

    @classmethod
    @ModelView.button_action('timetracker.act_start_work')
    def start_work_wizard(cls, tasks):
        pass

    def start_work(self):
        Line = Pool().get('timesheet.line')
        User = Pool().get('res.user')
        user = User(Transaction().user)
        line = Line()
        line.work = self.work.id
        line.start = datetime.datetime.now().time()
        line.hours = 0
        line.employee = user.employee.id
        line.save()

    @classmethod
    @ModelView.button
    def cancel_work(cls, tasks):
        Line = Pool().get('timesheet.line')
        Line = Pool().get('timesheet.line')
        User = Pool().get('res.user')
        user = User(Transaction().user)

        lines = Line.search([
                ('work', 'in', [x.work.id for x in tasks]),
                ('employee', '=', user.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])
        Line.delete(lines)
        return

    @classmethod
    @ModelView.button
    def stop_work(cls, tasks):
        Line = Pool().get('timesheet.line')
        User = Pool().get('res.user')
        user = User(Transaction().user)

        lines = Line.search([
                ('work', 'in', [x.work.id for x in tasks]),
                ('employee', '=', user.employee.id),
                ('start', '!=', None),
                ('end', '=', None),
                ])
        for line in lines:
            line.stop()
