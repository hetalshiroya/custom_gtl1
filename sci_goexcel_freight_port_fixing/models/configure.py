from odoo import models, fields, api
from odoo.exceptions import Warning


class Port(models.Model):
    _inherit = 'freight.ports'


    name1 = fields.Char(string='Temp Name')
    code1 = fields.Char(string='Temp Code')

    @api.multi
    def action_copy_old2new(self):
        ports = self.env['freight.ports'].sudo().search([])
        for port in ports:
            port.write({'name1': port.code,
                         'code1': port.name,
                         })

    @api.multi
    def action_copy_new2old(self):
        ports = self.env['freight.ports'].sudo().search([])
        for port in ports:
            port.write({'name': port.name1,
                        'code': port.code1,
                        })

