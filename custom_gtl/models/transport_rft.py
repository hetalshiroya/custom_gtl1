from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class TransportRFT(models.Model):
    _inherit = "transport.rft"

    job_type_trip = fields.Selection([('laden', 'Laden'),
                                      ('empty', 'Empty'),
                                      ('one_way', 'One Way'),
                                      ('round_trip', 'Round Trip')
                                      ], string='Job Type / Trip', default="one_way", track_visibility='onchange')

    special_handling = fields.Selection([('dg', 'DG'),
                                        ('reefer', 'REEFER'),
                                        ('oog', 'OOG'),
                                        ('side_loader', 'SIDE LOADED'),
                                        ('direct_delivery', 'DIRECT DELIVERY'),
                                        ('direct_loading', 'DIRECT LOADING')],
                                        string='Special Handling', default="direct_loading", track_visibility='onchange')
    scn_terminal_code = fields.Char(string='SCN/Terminal Code', track_visibility='onchange')
    off_load_at_premises = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Off Load At Premises')
    lcl_container = fields.Char(string='Container Qty/Type', track_visibility='onchange')