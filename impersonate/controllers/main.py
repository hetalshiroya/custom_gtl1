# -*- coding: UTF-8 -*-

from odoo import http
from odoo.http import request
from odoo.service import security

class WebClient(http.Controller):

    @http.route('/impersonate/exit', type='json', auth='user')
    def impersonate_exit(self):
        sess = request.session
        sess.uid = sess.impersonator_uid
        sess.login = sess.impersonator_login
        del sess['impersonator_uid']
        del sess['impersonator_login']
        request.env['res.users']._invalidate_session_cache()
        sess.session_token = security.compute_session_token(request.session, request.env)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
