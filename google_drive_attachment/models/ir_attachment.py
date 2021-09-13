# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import models, fields, api
from odoo.addons.google_drive.models.google_drive import GoogleDrive
import json
import requests


class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    file_id = fields.Char()
    folder_id = fields.Char()

    @api.multi
    def create_folder_on_google_drive(self, folder_name, model_obj=None):
        url = 'https://www.googleapis.com/drive/v3/files'
        g_drive = self.env['google.drive.config']
        access_token = GoogleDrive.get_access_token(g_drive)
        headers = {
            'Authorization': 'Bearer {}'.format(access_token),
            'Content-Type': 'application/json'
        }
        params = self.env['ir.config_parameter']
        folder_id = self.env['multi.folder.drive'].search([('model_id.model', '=', model_obj), ('company_id', '=', self.env.user.company_id.id)], limit=1).folder_id
        parent_id = folder_id
        if not parent_id:
            parent_id = self.company_id.drive_folder_id
            if not parent_id:
                parent_id = params.get_param('drive_folder_id')
        metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        response = requests.post(url, headers=headers, data=json.dumps(metadata))
        if response.status_code == 200:
            des = response.text.encode("utf-8")
            d = json.loads(des)
            return d.get('id')

    @api.model
    def create(self, vals):
        res = super(IrAttachment, self).create(vals)
        model_ids = self.env.user.company_id.model_ids.ids
        active_model = res.res_model
        m_id = self.env['ir.model'].search([('model', '=', active_model)])
        m_id = m_id and m_id.id or False
        if active_model in model_ids and res.name != 'thumbnail' and active_model != 'mail.compose.message':
            # if res.name != 'thumbnail':
            company_id = self.env.user.company_id
            active_id = res.res_id
            # params = self.env['ir.config_parameter']
            folder = company_id.folder_type
            if folder == 'single_folder':
                parent_id = company_id.drive_folder_id
            if folder == 'multi_folder':
                m_folder_id = self.env['multi.folder.drive'].search([
                    ('model_id.model', '=', active_model), ('company_id', '=', company_id.id)], limit=1)
                parent_id = m_folder_id.folder_id and m_folder_id.folder_id or company_id.drive_folder_id
            if folder == 'record_wise_folder':
                rec_id = self.env[active_model].browse(active_id)
                attachment = self.env['ir.attachment'].search([('res_model', '=', active_model), ('res_id', '=', active_id), ('folder_id', '!=', False), ('company_id', '=', company_id.id)])
                if not attachment:
                    parent_id = self.create_folder_on_google_drive(rec_id.name and rec_id.name or res.res_name, active_model)
                    res.folder_id = parent_id
                else:
                    parent_id = attachment.folder_id
            if parent_id:
                file_url = self.env['google.file.upload'].upload_to_google_drive(
                    res.name, res.datas, parent_id)
                if file_url:
                    res.datas = False
                    res.type = 'url'
                    res.url = file_url.get('url')
                    res.file_id = file_url.get('file_id')
                    self.env['ir.attachment']._file_gc()
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.file_id:
                self.env['google.file.upload'].delete_from_google_drive(
                    rec.file_id)
            self.env['ir.attachment']._file_gc()
        return super(IrAttachment, self).unlink()

    def write(self, value):
        self.env['ir.attachment']._file_gc()
        return super(IrAttachment, self).write(value)
