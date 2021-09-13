from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    #carrier = fields.Boolean(string="Is Carrier?")
    #shipper = fields.Boolean(string="Is Shipper?")
    #transporter = fields.Boolean(string="Is Transporter?")
    #consignee = fields.Boolean(string="Is Consignee?")
    forwarding_agent = fields.Boolean(string="Is Forwarding Agent?")
    container_operator = fields.Boolean(string="Is Container Operator?")
    #shipping_agent = fields.Boolean(string="Is Shipping Agent?")

    company_rft_count = fields.Integer(compute='_compute_company_rft_count')

    def _compute_company_rft_count(self):
        for partner in self:
            rft = self.env['transport.rft'].search([
                ('customer_name', '=', partner.id),
            ])
            partner.company_rft_count = len(rft)