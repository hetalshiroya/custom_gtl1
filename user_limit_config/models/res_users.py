# -*- coding: utf-8 -*-
from odoo import tools, api, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Done By Laxicon Solution - Shivam
    @api.model
    def create(self, vals):
        users = len(self.env['res.users'].search([('active', '=', True), ('id', '!=', 2), ('share', '=', False)]))
        user_limits = int(tools.config.get('user_limits'))
        if user_limits <= users:
            raise UserError("Maximum number of users created. Please contact to your system administrator!")
        res = super(ResUsers, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if vals.get('active'):
            users = len(self.env['res.users'].search([('active', '=', True), ('id', '!=', 2), ('share', '=', False)]))
            user_limits = int(tools.config.get('user_limits'))
            if user_limits <= users:
                raise UserError("Maximum number of users created. Please contact to your system administrator!")
        return res
