from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    carrier = fields.Boolean(string="Is Carrier?")
    shipper = fields.Boolean(string="Is Shipper?")
    transporter = fields.Boolean(string="Is Transporter?")
    consignee = fields.Boolean(string="Is Consignee?")
    #forwarding_agent = fields.Boolean(string="Is Forwarding Agent?")
    shipping_agent = fields.Boolean(string="Is Shipping Agent?")
    #over_credit = fields.Boolean('Allow Over Credit?', default=1)
    #over_credit = fields.Boolean('Allow Over Credit?')

    company_booking_count = fields.Integer(compute='_compute_company_booking_count')

    def _compute_company_booking_count(self):
        for partner in self:
            bookings = self.env['freight.booking'].search([
                ('customer_name', '=', partner.id),
            ])
            partner.company_booking_count = len(bookings)