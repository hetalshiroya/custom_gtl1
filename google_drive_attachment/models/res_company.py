# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    drive_folder_id = fields.Char(
        string='Folder ID', help="make a folder on drive in which you want to upload files; then open that folder; the last thing in present url will be folder id")
    folder_type = fields.Selection([('single_folder', 'Single Folder'),
                                    ('multi_folder', 'Multi Folder'),
                                    ('record_wise_folder', 'Record wise Folder')], default='single_folder')
    model_ids = fields.Many2many('ir.model', string='Models')
