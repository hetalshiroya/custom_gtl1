from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class BillOfLading(models.Model):
    _inherit = "freight.bol"

    changed_consignee = fields.Text(string='Changed Consignee')
    changed_shipper = fields.Text(string='Changed Shipper')
    original_shipper = fields.Text(string='Original Shipper')
    original_consignee = fields.Text(string='Original Consignee')
    changed_description = fields.Char(string='DESCRIPTION')
    changed_gross_weight = fields.Char(string='GROSS WEIGHT')
    changed_measurement = fields.Char(string='MEASUREMENT')
    changed_date = fields.Date(string='Date')

    changed_to = fields.Char(string='TO')
    changed_tel = fields.Char(string='TEL')
    changed_attn = fields.Char(string='ATTN')
    changed_from = fields.Char(string='FROM')

    @api.multi
    def action_correction_manifest(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_correction_manifest.correction_manifest_view_form')
        return {
            'name': 'Create Correction Manifest',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'correction.manifest',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

            'context': dict(bl_id=self.id),
        }

