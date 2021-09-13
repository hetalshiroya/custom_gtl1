from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class WarehouseLoadingPlan(models.Model):
    """Warehouse Loading Plan Model."""

    _name = 'warehouse.loading.plan'
    _description = 'Loading Plan'
    _order = 'job_no desc, write_date desc'
    color = fields.Integer('Color Index', default=0, store=False)
    _inherit = ['mail.thread', 'mail.activity.mixin']

    sequence = fields.Integer(string="sequence")
    job_no = fields.Char(string='Job No', copy=False, readonly=True, index=True)
    loading_date = fields.Datetime(string='Loading Date', track_visibility='onchange', copy=False,
                                   index=True)
    job_status = fields.Selection([('01', 'Draft'),
                                   ('02', 'Confirmed'), ('04', 'Done'), ('03', 'In Progress'),('05', 'Cancelled')], string="Job Status",
                                  default="01", copy=False,
                                  track_visibility='onchange', store=True)
    ts_reference = fields.Many2one('warehouse.tally.sheet', string='Job Sheet Ref', track_visibility='onchange', copy=False,
                                   index=True)
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')
    marking = fields.Text(string="Marking/Label", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    no_of_packages = fields.Integer(string="No. of Packages", track_visibility='onchange')
    no_of_package_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    warehouse_location = fields.Many2one('stock.location', string='Location', track_visibility='onchange')
    transporter = fields.Many2one('res.partner', string='Transporter Company', help="The Party who transport the goods from one place to another",
                              track_visibility='onchange')
    truck_no = fields.Char(string="Truck No.", track_visibility='onchange')
    driver = fields.Char(string="Driver", track_visibility='onchange')
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', select=True, default='2', track_visibility='onchange')
    owner = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user.id,
                            track_visibility='onchange')
    remark = fields.Text(string='Remark', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        vals['job_no'] = self.env['ir.sequence'].next_by_code('loadingplan')
        res = super(WarehouseLoadingPlan, self).create(vals)
        return res

    @api.multi
    def name_get(self):
        result = []
        for loadingplan in self:
            name = str(loadingplan.job_no)
        result.append((loadingplan.id, name))
        return result

    @api.multi
    def action_cancel_loadingplan(self):
        self.job_status = '05'