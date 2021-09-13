from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    context_default_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Default Warehouse', company_dependent=True,
        help="Default warehouse for GoExcel Logistic Warehouse.")

    # context_default_receipt_location_id = fields.Many2one(
    #     'stock.location', string='Default Warehouse', company_dependent=True,
    #     help="Default Inward Receipt Location")
    #
    # context_default_delivery_location_id = fields.Many2one(
    #     'stock.location', string='Default Outward Loading/Unloading Location', company_dependent=True,
    #     help="Default Outward Loading/Unloading Location")