# -*- coding: utf-8 -*-
# Part of Laxicon Solution. See LICENSE file for full copyright and
# licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    drive_folder_id = fields.Char(related='company_id.drive_folder_id', readonly=False,
                                  help="make a folder on drive in which you want to upload files; then open that folder; the last thing in present url will be folder id")
    folder_type = fields.Selection(
        related='company_id.folder_type', readonly=False, default='single_folder')
    model_ids = fields.Many2many(
        'ir.model', related='company_id.model_ids', readonly=False, string="Models")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']
        params_obj.sudo().set_param("drive_folder_id", self.drive_folder_id)
        params_obj.sudo().set_param("folder_type", self.folder_type)
        params_obj.sudo().set_param("model_ids", self.model_ids.ids)
