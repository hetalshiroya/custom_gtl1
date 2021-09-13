from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    sq_tally_sheet_count = fields.Integer(compute='_compute_sq_tally_sheet_count')
    sq_type = fields.Selection([('logistics', 'Logistics'), ('warehouse', 'Warehouse')], string="SQ Type", track_visibility='onchange')

    contact_name = fields.Many2one('res.partner', string='Contact Name', track_visibility='onchange')
    sq_description = fields.Char(string='SQ Description', track_visibility='onchange')
    show_subtotal = fields.Boolean('Show Subtotal', default=True)
    split_signature = fields.Boolean('Split Signature')

    @api.multi
    def _compute_sq_tally_sheet_count(self):
        for sq in self:
            tally_sheets = self.env['warehouse.tally.sheet'].search([
                ('sq_reference', '=', sq.id),
            ])
            sq.sq_tally_sheet_count = len(tally_sheets)


    @api.multi
    def action_copy_to_tally_sheet(self):
        tally_sheet_obj = self.env['warehouse.tally.sheet']
        tally_sheet_val = {
            'job_status': '01',
            'customer': self.partner_id.id or False,
            'sq_reference': self.id,
            'company_id': self.company_id.id,
            'sales_person': self.user_id.id,
        }

        tally_sheet = tally_sheet_obj.create(tally_sheet_val)
        cost_profit_obj = self.env['warehouse.cost.profit']
        for line in self.order_line:
            #_logger.warning('action_copy_to_booking 1')
            if line.product_id:
                #_logger.warning('action_copy_to_booking 2')

                if line.freight_foreign_price > 0.0:
                    price_unit = line.freight_foreign_price
                else:
                    price_unit = line.price_unit
                cost_profit_line = cost_profit_obj.create({
                    'product_id': line.product_id.id or False,
                    'product_name': line.name or False,
                    'tallysheet_id': tally_sheet.id or '',
                    'profit_qty': line.product_uom_qty or 0,
                    'profit_currency': line.freight_currency.id,
                    'profit_currency_rate': line.freight_currency_rate or 1.0,
                    'list_price': price_unit or 0.0,
                   # 'sale_total': line.price_unit or 0.0,

                })
                # booking.write({'booking_id': booking.id or False,
                #             'cost_profit_ids': cost_profit_line.id or False})
                tally_sheet.write({'cost_profit_ids': cost_profit_line or False})

        self.state = 'sale'

    @api.multi
    def view_sq_tally_sheet(self):
        """Show tally sheet smart Button."""
        for operation in self:
            tally_sheets = self.env['warehouse.tally.sheet'].search([
                ('sq_reference', '=', operation.id),
            ])
        print('len sq_reference=' + str(len(tally_sheets)))
        if len(tally_sheets) > 1:
            views = [(self.env.ref('sci_goexcel_warehouse.view_tree_warehouse_tally_sheet').id, 'tree'),
                     (self.env.ref('sci_goexcel_warehouse.view_form_warehouse_tally_sheet').id, 'form')]
            return {
                'name': 'Job Sheet',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'warehouse.tally.sheet',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', tally_sheets.ids)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(tally_sheets) == 1:
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'warehouse.tally.sheet',
                'res_id': tally_sheets.id or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }



class SaleQuotationLine(models.Model):
    _inherit = 'sale.order.line'

    freight_currency = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id,
                                        track_visibility='onchange')
    freight_foreign_price = fields.Float(string='Unit Price(FC)', track_visibility='onchange')
    freight_currency_rate = fields.Float(string='Conversion Rate', default="1.00", track_visibility='onchange')