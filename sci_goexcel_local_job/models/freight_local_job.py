from odoo import api, fields, models,exceptions
import logging
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    # direction = fields.Selection([('import', 'Import'), ('export', 'Export'), ('transhipment', 'Transhipment'),('local', 'local')],
    #                              string="Direction", default="import", track_visibility='onchange')

    def _get_default_job_category(self):
        #print('_get_default_job_category')
        job_categ = self.env['freight.booking'].browse(self.env.context.get('default_job_category'))
        #print('job_category=' + job_categ)
        if job_categ:
            self.job_category = job_categ

    job_category = fields.Selection([('freight', 'Freight Job'), ('local', 'Local Job')],
                                 string="Job Category", default=_get_default_job_category, track_visibility='onchange')
    local_job_no = fields.Char(string='Local Job No', copy=False, store=True)
    job_type = fields.Selection([('01', 'Consultation'), ('02', 'Insurance'), ('03', 'Warehousing'), ('04', 'Other')],
                                 string="Job Type", default="01", track_visibility='onchange')
    job_description = fields.Text(string='Job Description', track_visibility='onchange')
    local_job_status = fields.Selection([('01', 'New'), ('02', 'In Progress'), ('03', 'Done'), ('04', 'Cancelled')],
                                        string="Local Job Status", default="01", copy=False, track_visibility='onchange', store=True)
    start_date = fields.Date(string='Start Date', copy=False, default=datetime.now().date(), track_visibility='onchange')
    completion_date = fields.Date(string='Completion Date', copy=False, track_visibility='onchange')

    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False)
    account_date = fields.Date("Accounting Date",
                               readonly=True, index=True, help="Effective date for accounting entries", copy=False,
                               default=fields.Date.context_today)

    #@api.model
    #def create(self, vals):
    #     vals['dispatch_job_no'] = self.env['ir.sequence'].next_by_code('dj')
    #     res = super(DispatchJob, self).create(vals)
    #     return res

    @api.multi
    def name_get(self):
        result = super(FreightBooking, self).name_get()
        #print('name_get:' + str(result))
        for operation in self:
            if operation.job_category == 'local':
                result = []
                name = str(operation.local_job_no)
                result.append((operation.id, name))

        return result

    @api.multi
    def action_cancel_local_job(self):
        self.local_job_status = '04'

    """
    @api.onchange('job_category')
    def onchange_job_category(self):
        #print('job_Cat=' + self.job_category)
        if self.job_category == 'local':
            self.local_job_no = self.env['ir.sequence'].next_by_code('lj')
    """

    @api.model
    def create(self, vals):
        job_category = vals.get('job_category')
        if job_category == 'local':
            vals['local_job_no'] = self.env['ir.sequence'].next_by_code('lj')
        res = super(FreightBooking, self).create(vals)
        return res
