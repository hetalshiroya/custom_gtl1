# -*- coding: UTF-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.service import security

import logging
_logger = logging.getLogger(__name__)



class Impersonate(models.TransientModel):
    _name = 'impersonate'
    _description = 'Impersonate Wizard'


    user_id = fields.Many2one(
        comodel_name='res.users',
        required=True,
        domain=lambda self: self.env.user._impersonate_domain(),
    )

    @api.multi
    def apply(self):
        self.ensure_one()

        current_user = self.env.user
        requested_user = self.sudo().user_id

        if not current_user.impersonate_check(uid=requested_user.id):
            raise AccessDenied

        sess = request.session

        # backup original session info
        sess.impersonator_uid = sess.uid
        sess.impersonator_login = sess.login

        sess.uid = requested_user.id
        sess.login = requested_user.login

        request.env['res.users']._invalidate_session_cache()
        sess.session_token = security.compute_session_token(request.session, request.env)

        _logger.info('User %s (%s) started impersonating %s (%s)' % 
                     (current_user.name, current_user.id, requested_user.name, requested_user.id))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

