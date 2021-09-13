from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

class LoadingPlanWizard(models.TransientModel):
    _name = 'loading.plan.wizard'

    #split_booking_no = fields.Char(string='Split Booking No', index=True)
    container_line_loadingplan_ids2 = fields.One2many('loading.plan.line.wizard', 'container_loadingplan_line_id2',
                                                 string="Loading Plan Form")
    job_no = fields.Char(string='Job No', index=True)
    #warehouse_container_line_id2 = fields.Many2one('warehouse.container.line')

    @api.model
    def default_get(self, fields):
        result = super(LoadingPlanWizard, self).default_get(fields)
        tallysheet_id = self.env.context.get('tallysheet_id')
        if tallysheet_id :
            tallysheet = self.env['warehouse.tally.sheet'].browse(tallysheet_id )
            tallysheet_list = []
            for tallysheet_line in tallysheet.container_line_ids:
                if not tallysheet_line.add_to_loading_plan:
                    tallysheet_list.append({
                        'container_loadingplan_line_id2': tallysheet_line.id,
                        'container_product_id': tallysheet_line.container_product_id.id,
                        'product': tallysheet_line.product.id,
                        'container_no': tallysheet_line.container_no,
                        'marking': tallysheet_line.marking,
                        'seal_no': tallysheet_line.seal_no,
                        'no_of_packages': tallysheet_line.no_of_packages,
                        'no_of_package_uom': tallysheet_line.no_of_package_uom,
                        'warehouse_location': tallysheet_line.warehouse_location.id,
                    })
            result.update({'job_no': tallysheet.job_no,
                           })
            result['container_line_loadingplan_ids2'] = tallysheet_list
            result = self._convert_to_write(result)

        return result

    @api.multi
    def action_create_loading_plan(self):
        if self.job_no:
            #tallysheet = self.env['warehouse.tally.sheet'].search([('job_no', '=', self.job_no)])
            create_loading_plan = False
            for loadingplan in self.container_line_loadingplan_ids2:
                if loadingplan.add_to_loading_plan:
                    create_loading_plan = True

            if create_loading_plan:
                lp_obj = self.env['warehouse.loading.plan']

                lp_val = {
                    'container_product_id': loadingplan.container_product_id.id,
                    #'product': loadingplan.product,
                    'container_no': loadingplan.container_no,
                    'marking': loadingplan.marking,
                    'seal_no': loadingplan.seal_no,
                    'no_of_packages': loadingplan.no_of_packages,
                    'no_of_package_uom': loadingplan.no_of_package_uom.id,
                    'warehouse_location': loadingplan.warehouse_location.id,
                    'loading_date': loadingplan.loading_date,
                    'transporter': loadingplan.transporter.id,
                    'truck_no': loadingplan.truck_no,
                    'driver': loadingplan.driver,
                    'ts_reference': self.id,
                }
                loadingplan = lp_obj.create(lp_val)


class LoadingPlanLineWizard(models.TransientModel):

    _name = 'loading.plan.line.wizard'
    container_loadingplan_line_id2 = fields.Many2one('loading.plan.wizard', 'Container Loading Plan')

    sequence = fields.Integer(string="sequence")
    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange')
    product = fields.Many2one('product.product', string='Product', track_visibility='onchange')

    container_no = fields.Char(string="Container No.", track_visibility='onchange')

    marking = fields.Text(string="Marking/Label", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    no_of_packages = fields.Integer(string="No. of Packages", track_visibility='onchange')
    no_of_package_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    warehouse_location = fields.Many2one('stock.location', string='Location', track_visibility='onchange')
    loading_date = fields.Datetime(string='Loading Date', track_visibility='onchange', copy=False)
    transporter = fields.Many2one('res.partner', string='Transporter Company',
                                  help="The Party who transport the goods from one place to another")
    truck_no = fields.Char(string="Truck No.", track_visibility='onchange')
    driver = fields.Char(string="Driver", track_visibility='onchange')

    add_to_loading_plan = fields.Boolean(string='Add to Loading Plan')