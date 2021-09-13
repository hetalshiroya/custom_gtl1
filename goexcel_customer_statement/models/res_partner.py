from odoo import models,fields, api
from odoo import tools
class res_partner(models.Model):
    _inherit ='res.partner'

    overdue_date = fields.Date(string='Overdue Date')
    invoice_start_date = fields.Date(string='Invoice Date')
    aging_by = fields.Selection([('inv_date','Invoice Date'),('due_date','Due Date')],string='Aging By')
    aging_group = fields.Selection([('by_month', 'By Month'), ('by_days', 'By Days')], string='Ageing Group')
    account_type = fields.Selection([('ar','Receivable'),('ap','Payable'), ('both', 'Both')],string='Account Type')
    soa_note = fields.Text(string='SOA Note', track_visibility='onchange', compute="_get_use_soa_note")
    soa_type = fields.Selection([('all', 'All'), ('unpaid_invoices', 'Unpaid Invoices Only')], string='SOA Type')

    @api.multi
    def _get_use_soa_note(self):
        for record in self:
            # TS
           record.soa_note = self.env.user.company_id.soa_note