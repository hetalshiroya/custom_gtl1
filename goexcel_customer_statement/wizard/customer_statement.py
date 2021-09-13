from odoo import api, fields, models, _
import datetime
import calendar
from dateutil.relativedelta import *
import logging
_logger = logging.getLogger(__name__)
     

class customer_statement(models.TransientModel):
    _name = "customer.statement"

    soa_type = fields.Selection([('all', 'All'), ('unpaid_invoices', 'Unpaid Invoices Only')], string='SOA Type', default='all', required="1")
    invoice_start_date = fields.Date(string='Invoice Start Date', default=datetime.date.today().replace(day=1))
    invoice_end_date = fields.Date(string='Invoice End Date', default=str(datetime.date.today() + relativedelta(months=+1, day=1, days=-1))[:10])
    # month = fields.Selection([('1','JAN'),('2','FEB'),('3','MAR'),('4','APR'),('5','MAY'),('6','JUN'),('7','JUL'),('8','AUG'),('9','SEP'),('10','OCT'),('11','NOV'),('12','DEC')], string='End Month (Current Year)')
    aging_by = fields.Selection([('inv_date','Invoice Date'),('due_date','Due Date')],string='Ageing By', default='inv_date', required="1")
    aging_group = fields.Selection([('by_month', 'By Month'), ('by_days', 'By Days')], string='Ageing Group', default='by_month', required="1")
    date_upto = fields.Date('Upto Date',required="1", default=datetime.date.today())
    account_type = fields.Selection([('ar','Receivable'),('ap','Payable'), ('both', 'Both')],string='Account Type', default='ar', required="1")

    #is_privious_year = fields.Boolean(string='Previous Year (End Month)')


    # @api.onchange('month','is_privious_year')
    # def onchange_month(self):
    #     if self.month:
    #         a= self.month
    #         a = int(a)
    #         date=datetime.datetime.now()
    #         if self.is_privious_year:
    #             month_end_date=datetime.datetime(date.year-1,a,1) + datetime.timedelta(days=calendar.monthrange(date.year-1,a)[1] - 1)
    #             self.date_upto = month_end_date.date()
    #         else:
    #             month_end_date=datetime.datetime(date.year,a,1) + datetime.timedelta(days=calendar.monthrange(date.year,a)[1] - 1)
    #             self.date_upto = month_end_date.date()


    def _get_last_day_of_month(self):
        for operation in self:
            end_date = datetime.datetime(datetime.date.today().year, datetime.date.today().month,
                                         calendar.mdays[datetime.date.today().month])
            self.invoice_end_date = end_date


    @api.multi
    def print_statement(self):
        partner = self.env['res.partner']
        part_ids=self._context.get('active_ids')
        partner_ids = partner.browse(part_ids)
        if partner_ids:
            partner_ids.write({'overdue_date': self.invoice_end_date, 'aging_by': self.aging_by, 'aging_group': self.aging_group,
                               'invoice_start_date': self.invoice_start_date, 'account_type': self.account_type, 'soa_type': self.soa_type})
            datas = {
                'form': partner_ids.ids,
                #'account':  {'account_type': self.account_type},
                'model': self._name,
                'ids': self.ids,
            }
            # datas = {
            #     'form': partner_ids.ids
            # }
        return self.env.ref('goexcel_customer_statement.report_customer_statement').report_action(self, data=datas)

    @api.multi
    def send_statement(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        _logger.warning('send email')
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
            ir_model_data.get_object_reference('goexcel_customer_statement', 'email_template_edi_customer_statement')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        _logger.warning("active_ids=" + str(self._context.get('active_ids')))
        partner_ids = self.env['res.partner'].browse(self._context.get('active_ids'))
        _logger.warning("partner_ids=" + str(partner_ids))
        if partner_ids:
            partner_ids.write({'overdue_date': self.invoice_end_date, 'aging_by': self.aging_by, 'aging_group': self.aging_group,
                               'invoice_start_date': self.invoice_start_date, 'account_type': self.account_type, 'soa_type': self.soa_type})
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': partner_ids[0].id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
			'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

