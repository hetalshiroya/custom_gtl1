# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import models, fields, api, _
from odoo.addons.google_drive.models.google_drive import GoogleDrive
from odoo.exceptions import UserError
import requests
import json


class MultiFolderDrive(models.Model):

    _name = 'multi.folder.drive'
    _description = 'Multi Folder on Drive'

    model_id = fields.Many2one('ir.model', 'Model')
    name = fields.Char('Folder Name')
    folder_id = fields.Char('Folder ID')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    @api.multi
    def create_folder_on_drive(self):
        url = 'https://www.googleapis.com/drive/v3/files'
        g_drive = self.env['google.drive.config']
        access_token = GoogleDrive.get_access_token(g_drive)
        headers = {
            'Authorization': 'Bearer {}'.format(access_token),
            'Content-Type': 'application/json'
        }
        parent_id = self.company_id.drive_folder_id
        if not parent_id:
            params = self.env['ir.config_parameter']
            parent_id = params.get_param('drive_folder_id')
        if not parent_id:
            raise UserError(_("Please Create Parent Folder on Google Drive And set in the Compnay"))
        metadata = {
            'name': self.name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = requests.post(url, headers=headers,
                                 data=json.dumps(metadata))
        if response.status_code == 200:
            des = response.text.encode("utf-8")
            d = json.loads(des)
            self.folder_id = d.get('id')
