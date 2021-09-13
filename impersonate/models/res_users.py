# -*- coding: UTF-8 -*-

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    impersonate_ids = fields.Many2many(
        comodel_name='res.users',
        relation='res_users_impersonate_rel',
        column1='res_users_id',
        column2='res_users_impersonate_id',
        string='Impersonate Users',
    )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):

        if self._context.get('impersonate_selection'):
            args = self.env.user._impersonate_domain()
            return super(ResUsers, self.sudo()).name_search(name=name, args=args, operator=operator, limit=limit)

        return super(ResUsers, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.multi
    def _impersonate_domain(self):
        self.ensure_one()
        domain = [('id', '!=', self.id)]

        if self.has_group('impersonate.group_impersonate_all'):
            return domain

        if self.impersonate_ids:
            domain.extend([('id', 'in', self.impersonate_ids.ids)])
            return domain

        return [('id', '=', False)]

    @api.multi
    def impersonate_check(self, uid=None):
        self.ensure_one()
        domain = self._impersonate_domain()

        if uid is not None:
            domain.extend([('id', '=', uid)])

        return bool(self.search(domain, count=True))

    @api.multi
    def write(self, values):
        res = super(ResUsers, self).write(values)
        if 'impersonate_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            self.has_group.clear_cache(self)

        return res

