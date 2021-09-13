# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def auto_fill_done_qty_from_reserved_qty(self):
        for picking in self:
            for move_line in picking.move_ids_without_package:
                for move_line_id in move_line.move_line_ids:
                    move_line_id.qty_done = move_line_id.product_uom_qty