from odoo import models,fields, api
from odoo import tools
class res_partner(models.Model):
    _inherit ='res.users'

    signature_image = fields.Binary(related="company_id.signature_image", string="Signature", readonly=False)


