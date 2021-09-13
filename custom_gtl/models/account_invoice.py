from odoo import api, fields, models, exceptions,_
import logging
from datetime import date
from odoo.tools import float_round
_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)


class GTLFreightInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_description = fields.Char(string='Invoice Description', track_visibility='onchange')
    x_product_category = fields.Many2one('product.category', string='Freight Booking', track_visibility='onchange')

    invoice_note = fields.Text(string='Invoice Additional Note', track_visibility='onchange',
                               compute="_get_use_invoice_note")
    document_attachments_ids = fields.One2many('document.attachments', 'invoice_id', string="Documents")
    folder_id = fields.Char()
    invoice_type = fields.Selection([('lorry', 'Truck'), ('without_lorry', 'Non-Truck')], default='without_lorry',
                                    string='Invoice Type')
    attn = fields.Many2one('res.partner', string='Attn', track_visibility='onchange')
    # TS
    freight_hbl = fields.Many2one('freight.bol', string='Booking HBL')
    # TS end

    @api.model
    def create(self, vals):
        if vals.get('type') == 'in_refund' or vals.get('type') == 'out_refund' or vals.get('type') == 'in_invoice':
            if self.freight_hbl:
                vals.update({'freight_hbl': self.freight_hbl.id})
        res = super(GTLFreightInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        #print('>>>>>>>>>>>>>>>>>> GTLFreightInvoice Write')
        #Refund
        for record in self:
            if vals.get('state') == 'open' and (record.type == 'in_refund' or record.type == 'out_refund'):
                for invoice_line in record.invoice_line_ids:
                    if not invoice_line.booking_line_id and invoice_line.invoice_id.freight_hbl:
                        price_unit = 0.00
                        if record.company_id.currency_id != record.currency_id:
                            if record.exchange_rate_inverse:
                                price_unit = invoice_line.price_unit
                                freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                                currency_id = invoice_line.invoice_id.currency_id
                            else:
                                raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                        else:  # invoice is in company currency
                            if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                                invoice_line.price_unit = float_round(
                                    invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                                    2, rounding_method='HALF-UP')
                            if invoice_line.freight_currency_rate != 1:
                                price_unit = float_round(
                                    invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                    2,
                                    rounding_method='HALF-UP')
                            else:
                                price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                         rounding_method='HALF-UP')
                            freight_currency_rate = invoice_line.freight_currency_rate
                            currency_id = invoice_line.freight_currency
                        if not invoice_line.booking_line_id and invoice_line.invoice_id.freight_hbl:
                            #cost_profit = self.env['freight.bol.cost.profit']
                            cost_profit = self.env['freight.bol.cost.profit']
                            if record.type == 'out_refund' and invoice_line.invoice_id.freight_hbl:
                                sale_line = cost_profit.create({
                                    'product_id': invoice_line.product_id.id,
                                    'product_name': invoice_line.name,
                                    'profit_qty': invoice_line.quantity,
                                    'list_price': -(price_unit),
                                    'added_to_invoice': True,
                                    'profit_currency_rate': freight_currency_rate,
                                    'profit_currency': currency_id.id,
                                    'booking_id': invoice_line.invoice_id.freight_hbl.id or False,
                                })
                                invoice_line.booking_line_id = sale_line
                            elif record.type == 'in_refund':
                                booking_id = False
                                if invoice_line.invoice_id.freight_hbl:
                                    booking_id = invoice_line.invoice_id.freight_hbl.id
                                elif invoice_line.freight_hbl:
                                    booking_id = invoice_line.freight_hbl.id
                                if booking_id:
                                    cost_line = cost_profit.create({
                                        'product_id': invoice_line.product_id.id,
                                        'product_name': invoice_line.name,
                                        'cost_price': -(price_unit) or 0,
                                        'cost_qty': invoice_line.quantity or False,
                                        'cost_currency': currency_id.id,
                                        'cost_currency_rate': freight_currency_rate,
                                        'added_to_invoice': True,
                                        'vendor_id': invoice_line.invoice_id.partner_id.id,
                                        'booking_id': booking_id or False,
                                    })
                                    invoice_line.booking_line_id = cost_line
                    if not invoice_line.booking_line_id and invoice_line.invoice_id.freight_hbl:
                        booking = self.env['freight.bol'].browse(invoice_line.invoice_id.freight_hbl.id)
                        if not booking.analytic_account_id:
                            # print('>>>> onchange_freight_hbl no analytic account')
                            values = {
                                'code': booking.booking_ref.booking_no,
                                'partner_id': booking.customer_name.id,
                                'name': '%s' % booking.bol_no,
                                'company_id': self.env.user.company_id.id,
                            }
                            analytic_account = self.env['account.analytic.account'].sudo().create(values)
                            booking.write({'analytic_account_id': analytic_account.id,
                                           })
                            invoice_line.account_analytic_id = analytic_account.id,
                        else:
                            # print('>>>> onchange_freight_hbl with AA')
                            invoice_line.account_analytic_id = booking.analytic_account_id.id

        if vals.get('state') == 'open':
            #print('>>>>>>>>>>>>>>>>>> GTLFreightInvoice Write Open')
            for operation in self:
                if operation.freight_booking:
                    booking = self.env['freight.booking'].search([
                        ('id', '=', operation.freight_booking.id)], limit=1)
                    # if self.reference and booking:
                    if booking:
                        #print('>>>>>>>>>>>>>>>>>> GTLFreightInvoice Write booking=', booking.booking_no)
                        booking.action_reupdate_booking_invoice_one()
                else:  # without freight_booking, ie, vendor bill
                    #print('>>>>>>>>>>>>>>>>>> Write Else')
                    sorted_recordset = operation.invoice_line_ids.sorted(key=lambda r: r.freight_booking)
                    booking_id = False
                    for line in sorted_recordset:
                        if line.freight_booking and line.freight_booking.id != booking_id:
                            booking = self.env['freight.booking'].search([
                                ('id', '=', line.freight_booking.id)], limit=1)
                            if booking:
                                booking.action_reupdate_booking_invoice_one()
                                booking_id = line.freight_booking.id
                #for hbl
                if operation.freight_hbl:
                    booking = self.env['freight.booking'].search([
                        ('id', '=', operation.freight_hbl.booking_ref.id)], limit=1)
                    # if self.reference and booking:
                    if booking:
                        booking.action_reupdate_booking_invoice_one()
                else:  # without freight_booking, ie, vendor bill
                    #print('>>>>>>>>>>>>>>>>>> Write Else')
                    sorted_recordset = operation.invoice_line_ids.sorted(key=lambda r: r.freight_hbl)
                    booking_id = False
                    for line in sorted_recordset:
                        if line.freight_hbl and line.freight_hbl.id != booking_id:
                            booking = self.env['freight.booking'].search([
                                ('id', '=', line.freight_hbl.booking_ref.id)], limit=1)
                            if booking:
                                booking.action_reupdate_booking_invoice_one()
                                booking_id = line.freight_hbl.id

        res = super(GTLFreightInvoice, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        #print("Invoice Unlink")
        for inv in self:
            for invoice_line in inv.invoice_line_ids:
                if invoice_line.booking_line_id:
                    cost_profit_line = self.env['freight.bol.cost.profit'].search([('id', '=', invoice_line.booking_line_id.id)],
                                                                         limit=1)
                    if self.type == 'in_invoice' and cost_profit_line:  #when delete a vendor bill item
                        #if there are multiple vendor bills assigned to the same job cost
                        if cost_profit_line.vendor_bill_ids and len(cost_profit_line.vendor_bill_ids) > 1:
                            vendor_bill_ids_list = []
                            total_qty = 0
                            for vendor_bill_id in cost_profit_line.vendor_bill_ids:
                                account_invoice_line = self.env['account.invoice.line'].search(
                                    [('invoice_id', '=', vendor_bill_id.id)])
                                for invoice_line_item in account_invoice_line:
                                    #if invoice_line_item.product_id == cost_profit_line.product_id:
                                    if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_hbl.id == invoice_line.freight_hbl.id):
                                        total_qty = total_qty + invoice_line_item.quantity
                                if vendor_bill_id.id != self._origin.id:
                                    vendor_bill_ids_list.append(vendor_bill_id.id)
                            if total_qty > 0:
                                cost_profit_line.write(
                                    {  # assuming cost_price will always be same for all vendor bills for same item
                                        # 'cost_price': round(price_unit, 2) or 0,
                                        'cost_qty': total_qty or False,
                                        # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                        # 'cost_currency': invoice_line.freight_currency.id,
                                        'added_to_invoice': True,
                                        # 'vendor_id': self.invoice_id.partner_id.id,
                                        'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                    })
                            # cost_profit.write({
                            #     'vendor_id_ids': [(3, self.partner_id.id)],
                            #     'vendor_bill_ids': [(3, self.id)],
                            #     'added_to_invoice': False,
                            # })
                        else: #if only 1 vendor bill
                            cost_profit_line.write({
                                'vendor_id': False,
                                'vendor_bill_ids': [(3, self.id)],
                                'added_to_invoice': False,
                                'cost_price': 0,
                                'cost_qty': 0,
                                'cost_currency_rate': 1.000000,
                                'cost_currency': False,
                            })
                # if self.type == 'in_refund':
                    #     cost_profit.write({
                    #         'vendor_bill_ids': [(3, self.id)],
                    #     })
                    #booking = self.env['freight.bol'].search([('id', '=', cost_profit.booking_id.id)], limit=1)
                    #booking.action_calculate_cost()
        return super(GTLFreightInvoice, self).unlink()




    #main purpose is to update the vendor_bill_ids in the cost&profit items
    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        print('_onchange_invoice_line_ids')
        # call super protected method
        res = super(GTLFreightInvoice, self)._onchange_invoice_line_ids()
        filtered_invoice_lines = self.invoice_line_ids.filtered(lambda r: not r.check_calculate_cost)
        for invoice_line in filtered_invoice_lines:
            is_first = False
            #('>>>>>>>>>>> onchange_invoice_line_ids=' + invoice_line.invoice_type)
            if invoice_line.booking_line_id and (invoice_line.invoice_type == 'in_invoice'
                                                 or invoice_line.invoice_type == 'in_refund') and not invoice_line.check_calculate_cost:
                print('>>>>>>>>>>> onchange_invoice_line_ids booking_line_id')
                if invoice_line.freight_hbl:
                    #print('>>>>>>>>>>> onchange_invoice_line_ids freight booking')
                #if invoice_line.freight_hbl and not invoice_line.check_calculate_cost:
                    cost_profit = self.env['freight.bol.cost.profit'].search([('id', '=', invoice_line.booking_line_id.id)],
                                                                         limit=1)
                    #print('>>>>>>>>>>> onchange_invoice_line_ids cost_profit')
                    if self._origin.id:
                        #if first time the cost_profit being assigned cost
                        if cost_profit and not cost_profit.vendor_bill_ids:
                            #print('>>>>>>>>>>> onchange_invoice_line_ids not cost_profit.vendor_bill_ids')
                            #print('>>>>>>>>>>> onchange_invoice_line_ids not cost_profit:', cost_profit.product_name)
                            vendor_bill_ids_list = []
                            vendor_bill_ids_list.append(self._origin.id)
                            #vendor_ids_list.append(self.partner_id.id)
                            #'vendor_bill_ids': [(4, self.invoice_id.id)]
                            #print('>>>>>>>>>>> before is_first id=', self._origin.id)
                            cost_profit.write({    #if first time, must add new and cannot replace (6, 0, _ ).
                                'vendor_bill_ids': [(4, self._origin.id)],
                            })
                            #print('>>>>>>>>>>> onchange_invoice_line_ids after First')
                            is_first = True
                            #TS - fix bug (Analytic Account is false when VCN is created)
                            if not invoice_line.freight_hbl.analytic_account_id:
                                # print('>>>> onchange_freight_hbl no analytic account')
                                values = {
                                    'code': invoice_line.freight_hbl.booking_ref.booking_no,
                                    'partner_id': invoice_line.freight_hbl.customer_name.id,
                                    'name': '%s' % invoice_line.freight_hbl.bol_no,
                                    'company_id': self.env.user.company_id.id,
                                }
                                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                                invoice_line.freight_hbl.write({'analytic_account_id': analytic_account.id,
                                               })
                                #TS bug fixed - sometimes account analytic not assigned
                                invoice_line.write({'account_analytic_id': analytic_account.id,})
                                #invoice_line.account_analytic_id = analytic_account.id,
                            else:
                                # print('>>>> onchange_freight_hbl with AA')
                                invoice_line.account_analytic_id = invoice_line.freight_hbl.analytic_account_id.id
                            invoice_line.check_calculate_cost = True
                            #print('>>>>>>>>>>> onchange_invoice_line_ids after WRITE to invoice line')
                        # if not first time the cost_profit being assigned (update from vendor bill)
                        # or second cost assignment from second vendor bill
                        #total_qty = cost_profit.cost_qty
                        if not invoice_line.check_calculate_cost:
                            #print('>>>>>>>>>>> onchange_invoice_line_ids with cost_profit.vendor_bill_ids NOT check_calculate_cost')
                            if cost_profit.vendor_bill_ids and not is_first:
                                #print('>>>>>>>>>>> onchange_invoice_line_ids with cost_profit.vendor_bill_ids')
                                vendor_bill_ids_list = []
                                for cost_profit_vendor_bill in cost_profit.vendor_bill_ids:
                                    if cost_profit_vendor_bill.id != self._origin.id:
                                        vendor_bill_ids_list.append(cost_profit_vendor_bill.id)
                                vendor_bill_ids_list.append(self._origin.id)
                                cost_profit.write({
                                    'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                 })
                                invoice_line.check_calculate_cost = True
                                # invoice_line.write({
                                #     'check_calculate_cost': True,
                                # })
                    else:
                        raise exceptions.ValidationError('Please Save the Invoice/Vendor Bill First and Proceed!!!')

        return res



class GTLAccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    freight_currency = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id,
                                        track_visibility='onchange')
    freight_foreign_price = fields.Float(string='Unit Price(FC)', track_visibility='onchange')
    #freight_currency_rate = fields.Float(string='Rate', default="1.000000", digit=dp.get_precision('Exchange Rate'))
    freight_currency_rate = fields.Float(string='Rate', default="1.000000", digits=(12,6))
    #TS
    freight_hbl = fields.Many2one('freight.bol', string='Booking HBL')
    #bl_line_id = fields.Many2one('freight.bol.cost.profit', copy=False)
    #TS end


    @api.onchange('freight_hbl')
    def onchange_freight_hbl(self):  # trigger second
        # print('>>>> onchange_price_subtotal 1')
        # vendor bill only
        # print('>>>>>>>>>>> onchange_price_subtotal freight_hbl: ', self.invoice_type)
        if self.freight_hbl and self.product_id and self.invoice_type == 'in_invoice' and not self.invoice_id.debit_invoice_id:
            booking = self.env['freight.bol'].search([('id', '=', self.freight_hbl.id)], limit=1)
            check_booking = False
            # print('>>>>>>>>>>  onchange_price_subtotal 2 booking.id=', booking.id)
            for cost_profit_line in booking.cost_profit_ids:
                # print('>>>>>>>>>>self.product_id', self.product_id, ' , cost_profit_line.product_id=', cost_profit_line.product_id)
                if cost_profit_line.product_id == self.product_id:
                    price_unit = 0
                    freight_currency_rate = 1.000000
                    currency_id = self.freight_currency
                    # print('>>>> onchange_freight_hbl equal')
                    # if not cost_profit_line.invoiced:
                    self.bl_line_id = cost_profit_line
                    check_booking = True
                    total_cost = 0
                    total_qty = 0
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        # print('>>>> onchange_price_subtotal price >0')
                        # if already have vendor bills that had assigned cost
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                # print('>>>>>>>>>>  onchange_price_subtotal vendor_bill_ids>1=', len(cost_profit_line.vendor_bill_ids))
                                total_qty = 0
                                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                                                                                     vendor_bill_line.id)])
                                    # print('>>>>>>>>>>  onchange_price_subtotal account_invoice_line=',
                                    #      len(account_invoice_line))
                                    for invoice_line_item in account_invoice_line:
                                        # print('>>>>>>>>>>  onchange_price_subtotal invoice_line_item.freight_hbl=',
                                        #     invoice_line_item.freight_hbl)
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_hbl.id == self.freight_hbl.id):
                                            total_qty = total_qty + invoice_line_item.quantity
                                            # print('>>>> onchange_price_subtotal price total_qty=', total_qty)
                                    if not account_invoice_line or len(account_invoice_line) == 0:
                                        total_qty = total_qty + self.quantity
                                if total_qty > 0:
                                    cost_profit_line.write(
                                        {  # assuming cost_price will always be same for all vendor bills for same item
                                            # 'cost_price': round(price_unit, 2) or 0,
                                            'cost_qty': total_qty or False,
                                            # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                            # 'cost_currency': invoice_line.freight_currency.id,
                                            'invoiced': True,
                                            # 'vendor_id': self.invoice_id.partner_id.id,
                                            # 'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                        })
                            else:  # First cost assignment from the vendor bill
                                if self.invoice_id.company_id.currency_id != self.invoice_id.currency_id:
                                    if self.invoice_id.exchange_rate_inverse:
                                        # price_unit = float_round(
                                        #     self.price_subtotal / self.quantity / self.invoice_id.exchange_rate_inverse,
                                        #     2,
                                        #     rounding_method='HALF-UP')
                                        price_unit = self.price_unit
                                        freight_currency_rate = self.invoice_id.exchange_rate_inverse
                                        currency_id = self.invoice_id.currency_id
                                    else:
                                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                                else:
                                    if self.freight_currency_rate != 1:
                                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                                        price_unit = float_round(
                                            self.price_subtotal / self.quantity / self.freight_currency_rate,
                                            2, rounding_method='HALF-UP')
                                    else:
                                        price_unit = float_round(self.price_subtotal / self.quantity, 2,
                                                                 rounding_method='HALF-UP')
                                    freight_currency_rate = self.freight_currency_rate
                                    currency_id = self.freight_currency
                                # if self.type == 'in_invoice':
                                # total_cost = total_cost + price_unit
                                # print('>>>>>>> _onchange_price freight_hbl price_unit:', price_unit)
                                # total_cost = price_unit  # formula is always cost_price * cost_qty
                                total_qty = self.quantity
                                cost_profit_line.write({
                                    'cost_price': price_unit,
                                    'cost_qty': total_qty,  # why add 1
                                    'invoiced': True,
                                    'vendor_id': self.invoice_id.partner_id.id,
                                    'vendor_bill_id': self.invoice_id.id,
                                    'cost_currency': currency_id.id,
                                    'cost_currency_rate': freight_currency_rate,
                                    # 'vendor_bill_ids': [(4, self.invoice_id.id)],
                                })

                        else:
                            # assign the cost for first vendor bill
                            # print('>>>> onchange_price_subtotal else')
                            if self.invoice_id.company_id.currency_id != self.invoice_id.currency_id:
                                if self.invoice_id.exchange_rate_inverse:
                                    # price_unit = float_round(
                                    #     self.price_subtotal / self.quantity / self.invoice_id.exchange_rate_inverse,
                                    #     2,
                                    #     rounding_method='HALF-UP')
                                    price_unit = self.price_unit
                                    freight_currency_rate = self.invoice_id.exchange_rate_inverse
                                    currency_id = self.invoice_id.currency_id
                                else:
                                    raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                            else:
                                if self.freight_currency_rate != 1:
                                    # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                                    price_unit = float_round(
                                        self.price_subtotal / self.quantity / self.freight_currency_rate,
                                        2, rounding_method='HALF-UP')
                                else:
                                    price_unit = float_round(self.price_subtotal / self.quantity, 2,
                                                             rounding_method='HALF-UP')
                                freight_currency_rate = self.freight_currency_rate
                                currency_id = self.freight_currency
                            # if self.invoice_id.type == 'out_invoice':
                            #     cost_profit_line.write({
                            #         'list_price': price_unit or 0,
                            #         'profit_qty': self.quantity or False,
                            #         'profit_currency_rate': self.freight_currency_rate,
                            #     })
                            #
                            # elif self.invoice_id.type == 'in_invoice':

                            # print('>>>> onchange_freight_hbl price_unit=', str(price_unit))
                            # price_unit = invoice_line_item.price_subtotal / self.quantity
                            total_cost = total_cost + price_unit
                            total_qty += self.quantity
                            vendor_ids_list = []
                            # vendor_bill_ids_list = []
                            vendor_ids_list.append(self.invoice_id.partner_id.id)
                            # vendor_bill_ids_list.append(self.invoice_id.id)
                            # print('vendor_ids_list', vendor_ids_list)
                            # print('vendor_ids_list', vendor_bill_ids_list)
                            # print('new_parent_id', self.env.context.get('new_parent_id'))
                            # print('parent_id', self.inv_parent_id)
                            cost_profit_line.write({
                                'cost_price': float_round(total_cost, 2, rounding_method='HALF-UP'),
                                'cost_qty': total_qty,
                                'invoiced': True,
                                'vendor_id': self.invoice_id.partner_id.id,
                                'vendor_bill_id': self.invoice_id.id,
                                'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                # 'vendor_bill_ids': [(4, self.invoice_id._ids)],
                                # 'vendor_bill_ids': [(4, vendor_bill_ids_list)],
                            })

                    if not booking.analytic_account_id:
                        # print('>>>> onchange_freight_hbl no analytic account')
                        values = {
                            'code': booking.booking_ref.booking_no,
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.bol_no,
                            'company_id': self.env.user.company_id.id,
                        }

                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        self.account_analytic_id = analytic_account.id
                    else:
                        # print('>>>> onchange_freight_hbl with AA')
                        self.account_analytic_id = booking.analytic_account_id.id
            # if check_booking:
            #    booking.action_calculate_cost()
            if not check_booking:
                #TODO
                cost_profit_obj = self.env['freight.cost_profit']
                if self.freight_currency_rate != 1:
                    price_unit = float_round(
                        self.price_subtotal / self.quantity / self.freight_currency_rate,
                        2, rounding_method='HALF-UP')
                else:
                    price_unit = float_round(self.price_subtotal / self.quantity, 2,
                                             rounding_method='HALF-UP')
                cost_profit_line = cost_profit_obj.create({
                    'product_id': self.product_id.id or False,
                    'product_name': self.name or False,
                    'booking_id': booking.id or '',
                    'cost_qty': self.quantity or 0,
                    'cost_currency': self.freight_currency.id,
                    'cost_currency_rate': self.freight_currency_rate or 1.0,
                    'cost_price': float_round(price_unit, 2, rounding_method='HALF-UP'),
                    'vendor_id': self.invoice_id.partner_id.id or False,
                    'vendor_bill_id': self.invoice_id.id or 0.0,
                    'invoiced': True,
                })
                booking.write({'cost_profit_ids': cost_profit_line or False})
                if not booking.analytic_account_id:
                    # print('>>>> onchange_freight_booking no analytic account')
                    values = {
                        'partner_id': booking.customer_name.id,
                        'name': '%s' % booking.booking_no,
                        'company_id': self.env.user.company_id.id,
                    }
                    analytic_account = self.env['account.analytic.account'].sudo().create(values)
                    booking.write({'analytic_account_id': analytic_account.id,
                                   })
                    self.account_analytic_id = analytic_account.id
                else:
                    self.account_analytic_id = booking.analytic_account_id.id

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        # call super method
        print('onchange_price_unit')
        res = super(GTLAccountInvoiceLine, self).onchange_price_unit()
        for invoice_line in self:
            price_unit = 0
            freight_currency_rate = 1.000000
            currency_id = invoice_line.freight_currency
            # print('>>>>>>> _onchange_price_unit type=', invoice_line.invoice_id.type)
            # print('>>>>>>> _onchange_price_unit customer_debit_note=', invoice_line.invoice_id.customer_debit_note)
            ##print('>>>>>>> _onchange_price_unit debit_invoice_id=', invoice_line.invoice_id.debit_invoice_id)
            if invoice_line.invoice_id.type == 'out_invoice':  # invoice
                # if the invoice is in USD or other foreign currency
                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        # price_unit = float_round(
                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                        #     2,
                        #     rounding_method='HALF-UP')
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(
                            invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                            2, rounding_method='HALF-UP')
                    # print('>>>>>>> _onchange_price INVOICE')
                    # list_price = invoice_line.freight_foreign_price / invoice_line.freight_currency_rate
                    if invoice_line.freight_currency_rate != 1:
                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                        print('>>>>>>> _onchange_price price_unit 1:', price_unit)
                    else:
                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                # print('>>>>>>> _onchange_price price_unit 2:', price_unit)
                if invoice_line.invoice_id.freight_hbl:
                    # print('>>>>>>> _onchange_price booking')
                    booking = self.env['freight.bol'].browse(invoice_line.invoice_id.freight_hbl.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            # print('>>>>>>> _onchange_price product=', invoice_line.product_id.name)
                            cost_profit_line.write({
                                'list_price': price_unit,
                                'profit_qty': invoice_line.quantity or False,
                                'profit_currency_rate': freight_currency_rate,
                                'profit_currency': currency_id.id,
                            })
                            break

            elif invoice_line.invoice_id.type == 'in_invoice' and \
                    invoice_line.invoice_id.debit_invoice_id:  # vendor debit note
                # print('>>>>>>> _onchange_price_unit VDN')
                if invoice_line.invoice_id.freight_hbl:
                    booking_id = invoice_line.invoice_id.freight_hbl.id
                elif invoice_line.freight_hbl:
                    booking_id = invoice_line.freight_hbl.id

                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    if invoice_line.freight_currency_rate != 1:
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                    else:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                    # print('>>>>>>> _onchange_price_unit VDN price_unit ', price_unit)
                    # Update (if the DN line alrdy in the cost&profit)
                if invoice_line.bl_line_id and len(invoice_line.bl_line_id) > 0:
                    # print('>>>>>>> _onchange_price VCN Second time')
                    cost_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                    cost_line.write({
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.name,
                        'cost_price': price_unit or 0,
                        'cost_qty': invoice_line.quantity or False,
                        'cost_currency': currency_id.id,
                        'cost_currency_rate': freight_currency_rate,
                        'invoiced': True,
                        'vendor_id': invoice_line.invoice_id.partner_id.id,
                    })
                else:
                    # print('>>>>>>> _onchange_price VDN First time')
                    if booking_id:
                        cost_profit = self.env['freight.bol.cost.profit']
                        cost_line = cost_profit.create({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'cost_price': price_unit or 0,
                            'cost_qty': invoice_line.quantity or False,
                            'cost_currency': currency_id.id,
                            'cost_currency_rate': freight_currency_rate,
                            'invoiced': True,
                            'vendor_id': invoice_line.invoice_id.partner_id.id,
                            'booking_id': booking_id or False,
                        })
                        invoice_line.bl_line_id = cost_line
                booking = self.env['freight.bol'].browse(booking_id)
                if not booking.analytic_account_id:
                    # print('>>>> onchange_freight_hbl no analytic account')
                    values = {
                        'code': booking.booking_ref.booking_no,
                        'partner_id': booking.customer_name.id,
                        'name': '%s' % booking.bol_no,
                        'company_id': self.env.user.company_id.id,
                    }
                    analytic_account = self.env['account.analytic.account'].sudo().create(values)
                    booking.write({'analytic_account_id': analytic_account.id,
                                   })
                    invoice_line.account_analytic_id = analytic_account.id,
                else:
                    # print('>>>> onchange_freight_hbl with AA')
                    invoice_line.account_analytic_id = booking.analytic_account_id.id

            elif invoice_line.invoice_id.type == 'in_invoice':  # vendor bill
                # if vendor bill is created directly and assigned job line by line or when update qty/FC/price unit
                # print('>>>>>>> _onchange_price_unit in_invoice')
                if invoice_line.bl_line_id and not (
                        invoice_line.invoice_type == 'in_refund' or invoice_line.invoice_type == 'out_refund'):
                    cost_profit_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                # print('>>>>>>> _onchange_price_unit in_invoice > 1')
                                total_qty = 0
                                for vendor_bill_id in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search(
                                        [('invoice_id', '=', vendor_bill_id.id)])
                                    for invoice_line_item in account_invoice_line:
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_hbl.id == self.freight_hbl.id):
                                            # if invoice_line_item.product_id == cost_profit_line.product_id:
                                            total_qty = total_qty + invoice_line_item.quantity
                                            # account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                            #     vendor_bill_line.id)])
                                            #     for invoice_line_item in account_invoice_line:
                                            #         if invoice_line_item.bl_line_id == cost_profit_line:
                                            #             total_qty = total_qty + invoice_line_item.quantity
                                            # print('>>>>>>> _onchange_price_unit total qty=' + total_qty)
                                    if not account_invoice_line or len(account_invoice_line) == 0:
                                        total_qty = total_qty + self.quantity
                                if total_qty > 0:
                                    cost_profit_line.write(
                                        {  # assuming cost_price will always be same for all vendor bills for same item
                                            # 'cost_price': round(price_unit, 2) or 0,
                                            'cost_qty': total_qty or False,
                                            # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                            # 'cost_currency': invoice_line.freight_currency.id,
                                            'invoiced': True,
                                            # 'vendor_id': self.invoice_id.partner_id.id,
                                            # 'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                        })
                            else:  # First cost assignment from the vendor bill
                                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                                    if invoice_line.invoice_id.exchange_rate_inverse:
                                        # price_unit = float_round(
                                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                                        #     2,
                                        #     rounding_method='HALF-UP')
                                        price_unit = invoice_line.price_unit
                                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                                        currency_id = invoice_line.invoice_id.currency_id
                                    else:
                                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                                else:
                                    if invoice_line.freight_currency_rate != 1:
                                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                                        price_unit = float_round(
                                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                            2, rounding_method='HALF-UP')
                                    else:
                                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                                 rounding_method='HALF-UP')
                                    freight_currency_rate = invoice_line.freight_currency_rate
                                    currency_id = invoice_line.freight_currency
                                # if self.type == 'in_invoice':
                                # total_cost = total_cost + price_unit
                                # print('>>>>>>> _onchange_price_unit 222')
                                # total_cost = price_unit   #formula is always cost_price * cost_qty
                                total_qty = invoice_line.quantity
                                cost_profit_line.write({
                                    'cost_price': price_unit,
                                    'cost_qty': total_qty,  # why add 1
                                    'invoiced': True,
                                    'vendor_id': invoice_line.invoice_id.partner_id.id,
                                    'vendor_bill_id': invoice_line.invoice_id.id,
                                    'cost_currency': currency_id.id,
                                    'cost_currency_rate': freight_currency_rate,
                                    # 'vendor_bill_ids': [(4, self.invoice_id.id)],
                                })
                                # if self.type == 'in_refund':
                                #     #if invoice_line_item.bl_line_id == cost_profit_line:
                                #     total_cost = cost_profit_line.cost_total
                                #     #price_unit = invoice_line_item.price_subtotal / invoice_line_item.quantity
                                #     total_cost = total_cost + self.price_subtotal
                                #     #total_qty = total_qty - invoice_line_item.quantity
                                #     cost_profit_line.write({
                                #         'cost_total': round(total_cost, 2),
                                #     })
                        else:  # First cost assignment from the vendor bill
                            # print('>>>>>>> _onchange_price_unit in_invoice else')
                            if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                                if invoice_line.invoice_id.exchange_rate_inverse:
                                    # price_unit = float_round(
                                    #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                                    #     2,
                                    #     rounding_method='HALF-UP')
                                    price_unit = invoice_line.price_unit
                                    freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                                    currency_id = invoice_line.invoice_id.currency_id
                                else:
                                    raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                            else:
                                if invoice_line.freight_currency_rate != 1:
                                    price_unit = float_round(
                                        invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                        2, rounding_method='HALF-UP')
                                else:
                                    price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                             rounding_method='HALF-UP')
                                freight_currency_rate = invoice_line.freight_currency_rate
                                currency_id = invoice_line.freight_currency
                            cost_profit_line.write({
                                'cost_price': price_unit or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': invoice_line.invoice_id.partner_id.id,
                            })
                elif self.freight_hbl:  # if create vendor bill from job
                    if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                        if invoice_line.invoice_id.exchange_rate_inverse:
                            # price_unit = float_round(
                            #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                            #     2,
                            #     rounding_method='HALF-UP')
                            price_unit = invoice_line.price_unit
                            freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                            currency_id = invoice_line.invoice_id.currency_id
                        else:
                            raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                    else:
                        if invoice_line.freight_currency_rate != 1:
                            # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                            price_unit = float_round(
                                invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                2,
                                rounding_method='HALF-UP')
                        else:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                     rounding_method='HALF-UP')
                        freight_currency_rate = invoice_line.freight_currency_rate
                        currency_id = invoice_line.freight_currency

                    booking = self.env['freight.bol'].browse(self.freight_hbl.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            cost_profit_line.write({
                                'cost_price': price_unit or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': self.invoice_id.partner_id.id,
                                # 'vendor_bill_id': self.invoice_id.id,
                                # 'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
                            })
                            break

            elif invoice_line.invoice_id.type == 'out_refund':  # customer credit note
                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        # price_unit = float_round(
                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                        #     2,
                        #     rounding_method='HALF-UP')
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(
                            invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                            2, rounding_method='HALF-UP')
                    if invoice_line.freight_currency_rate != 1:
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                    else:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency

                if invoice_line.bl_line_id and len(
                        invoice_line.bl_line_id) > 0:  # Update (if the CN line alrdy in the cost&profit)
                    # print('>>>>>>> _onchange_price_unit bl_line_id >0')
                    cost_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                    cost_line.write({
                        'list_price': -(price_unit),
                        'profit_qty': invoice_line.quantity or False,
                        'profit_currency_rate': freight_currency_rate,
                        'profit_currency': currency_id.id,
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.name,
                    })
                else:
                    if invoice_line.invoice_id and invoice_line.freight_hbl:
                        # print('>>>>>>> _onchange_price_unit bl_line_id ==0')
                        cost_profit = self.env['freight.bol.cost.profit']
                        sale_line = cost_profit.create({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'profit_qty': invoice_line.quantity,
                            'list_price': -(price_unit),
                            'added_to_invoice': True,
                            'profit_currency_rate': freight_currency_rate,
                            'profit_currency': currency_id.id,
                            'booking_id': invoice_line.freight_hbl.id or False,
                        })
                        invoice_line.bl_line_id = sale_line

                if invoice_line.invoice_id and invoice_line.freight_hbl:
                    booking = self.env['freight.bol'].browse(invoice_line.freight_hbl.id)
                    if not booking.analytic_account_id:
                        # print('>>>> onchange_freight_hbl no analytic account')
                        values = {
                            'code': booking.booking_ref.booking_no,
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.bol_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        # print('>>>> onchange_freight_hbl with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id,

            elif invoice_line.invoice_id.type == 'in_refund':  # vendor credit note (refund)
                # print('>>>>>>> _onchange_price_unit VCN')
                booking_id = False
                if invoice_line.invoice_id.freight_hbl:
                    booking_id = invoice_line.invoice_id.freight_hbl.id
                elif invoice_line.freight_hbl:
                    booking_id = invoice_line.freight_hbl.id
                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        # price_unit = float_round(
                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                        #     2,
                        #     rounding_method='HALF-UP')
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    # if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                    #     invoice_line.price_unit = float_round(
                    #         invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                    #         2, rounding_method='HALF-UP')
                    if invoice_line.freight_currency_rate != 1:
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                    else:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                    # print('>>>>>>> _onchange_price_unit VCN price_unit ', price_unit)
                    # Update (if the CN line alrdy in the cost&profit)
                if booking_id:
                    if invoice_line.bl_line_id and len(invoice_line.bl_line_id) > 0:
                        # print('>>>>>>> _onchange_price VCN Second time')
                        cost_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                        cost_line.write({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'cost_price': -(price_unit) or 0,
                            'cost_qty': invoice_line.quantity or False,
                            'cost_currency': currency_id.id,
                            'cost_currency_rate': freight_currency_rate,
                            'invoiced': True,
                            'vendor_id': invoice_line.invoice_id.partner_id.id,
                        })
                    else:
                        # print('>>>>>>> _onchange_price VCN First time')
                        if booking_id:
                            cost_profit = self.env['freight.bol.cost.profit']
                            cost_line = cost_profit.create({
                                'product_id': invoice_line.product_id.id,
                                'product_name': invoice_line.name,
                                'cost_price': -(price_unit) or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': invoice_line.invoice_id.partner_id.id,
                                'booking_id': booking_id or False,
                            })
                            invoice_line.bl_line_id = cost_line
                    booking = self.env['freight.bol'].browse(invoice_line.freight_hbl.id)
                    if booking and not booking.analytic_account_id:
                        # print('>>>> onchange_freight_hbl no analytic account')
                        values = {
                            'code': booking.booking_ref.booking_no,
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.bol_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        invoice_line.account_analytic_id = analytic_account.id
                    elif booking and booking.analytic_account_id:
                        # print('>>>> onchange_freight_hbl with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id
        return res

    @api.onchange('freight_foreign_price', 'quantity', 'freight_currency_rate')
    def _onchange_price(self):  # trigger first

        # call super method
        print('onchange_price')
        res = super(GTLAccountInvoiceLine, self)._onchange_price()
        # print('>>>>>>> _onchange_price FC rate=', self.freight_currency_rate)
        # print('>>>>>>> _onchange_price FF price=', self.freight_foreign_price)
        # print('>>>>>>> _onchange_price rounded=', round(self.freight_currency_rate * self.freight_foreign_price, 2))
        # print('>>>>>>> _onchange_price price unit=', self.price_unit)
        for invoice_line in self:
            price_unit = 0
            freight_currency_rate = 1.000000
            currency_id = invoice_line.freight_currency
            if invoice_line.invoice_id.type == 'out_invoice':  # invoice
                # if the invoice is in USD or other foreign currency
                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        # price_unit = float_round(
                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse, 2,
                        #     rounding_method='HALF-UP')
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(
                            invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                            2, rounding_method='HALF-UP')
                    # print('>>>>>>> _onchange_price INVOICE')
                    # list_price = invoice_line.freight_foreign_price / invoice_line.freight_currency_rate
                    if invoice_line.freight_currency_rate != 1:
                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                        # print('>>>>>>> _onchange_price price_unit 1:', price_unit)
                    else:
                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                    print('>>>>>>> _onchange_price price_unit 2:', price_unit)
                if invoice_line.invoice_id.freight_hbl:
                    # print('>>>>>>> _onchange_price booking')
                    booking = self.env['freight.bol'].browse(invoice_line.invoice_id.freight_hbl.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            # print('>>>>>>> _onchange_price product=', invoice_line.product_id.name)
                            cost_profit_line.write({
                                'list_price': price_unit,
                                'profit_qty': invoice_line.quantity or False,
                                'profit_currency_rate': freight_currency_rate,
                                'profit_currency': currency_id.id,
                            })
                            break

            elif invoice_line.invoice_id.type == 'in_invoice' and \
                    invoice_line.invoice_id.debit_invoice_id:  # vendor debit note
                # print('>>>>>>> _onchange_price_unit VDN')
                if invoice_line.invoice_id.freight_hbl:
                    booking_id = invoice_line.invoice_id.freight_hbl.id
                elif invoice_line.freight_hbl:
                    booking_id = invoice_line.freight_hbl.id

                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(
                            invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                            2, rounding_method='HALF-UP')
                    if invoice_line.freight_currency_rate != 1:
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                    else:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                    # print('>>>>>>> _onchange_price_unit VDN price_unit ', price_unit)
                # Update (if the DN line alrdy in the cost&profit)
                if invoice_line.bl_line_id and len(invoice_line.bl_line_id) > 0:
                    # print('>>>>>>> _onchange_price VCN Second time')
                    cost_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                    cost_line.write({
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.name,
                        'cost_price': price_unit or 0,
                        'cost_qty': invoice_line.quantity or False,
                        'cost_currency': currency_id.id,
                        'cost_currency_rate': freight_currency_rate,
                        'invoiced': True,
                        'vendor_id': invoice_line.invoice_id.partner_id.id,
                    })
                    invoice_line.check_calculate_cost = True
                else:
                    # print('>>>>>>> _onchange_price VDN First time')
                    if booking_id:
                        cost_profit = self.env['freight.bol.cost.profit']
                        cost_line = cost_profit.create({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'cost_price': price_unit or 0,
                            'cost_qty': invoice_line.quantity or False,
                            'cost_currency': currency_id.id,
                            'cost_currency_rate': freight_currency_rate,
                            'invoiced': True,
                            'vendor_id': invoice_line.invoice_id.partner_id.id,
                            'booking_id': booking_id or False,
                        })
                        invoice_line.bl_line_id = cost_line
                booking = self.env['freight.bol'].browse(booking_id)
                if not booking.analytic_account_id:
                    # print('>>>> onchange_freight_hbl no analytic account')
                    values = {
                        'code': booking.booking_ref.booking_no,
                        'partner_id': booking.customer_name.id,
                        'name': '%s' % booking.bol_no,
                        'company_id': self.env.user.company_id.id,
                    }
                    analytic_account = self.env['account.analytic.account'].sudo().create(values)
                    booking.write({'analytic_account_id': analytic_account.id,
                                   })
                    invoice_line.account_analytic_id = analytic_account.id,
                else:
                    # print('>>>> onchange_freight_hbl with AA')
                    invoice_line.account_analytic_id = booking.analytic_account_id.id,
            elif invoice_line.invoice_id.type == 'in_invoice':  # vendor bill
                # if vendor bill is created directly and assigned job line by line or when update qty/FC/price unit
                # print('>>>>>>> _onchange_price in vendor bill')
                if invoice_line.bl_line_id and not (
                        invoice_line.invoice_type == 'in_refund' or invoice_line.invoice_type == 'out_refund'):
                    cost_profit_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(
                            invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                            2, rounding_method='HALF-UP')
                    # print('>>>>>>> _onchange_price in_invoice price_unit')
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                # print('>>>>>>> _onchange_price in_invoice > 1')
                                total_qty = 0
                                for vendor_bill_id in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                                                                                     vendor_bill_id.id)])
                                    for invoice_line_item in account_invoice_line:
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_hbl.id == self.freight_hbl.id):
                                            # if invoice_line_item.product_id == cost_profit_line.product_id:
                                            total_qty = total_qty + invoice_line_item.quantity
                                    if not account_invoice_line or len(account_invoice_line) == 0:
                                        total_qty = total_qty + self.quantity
                                    # account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                    #     vendor_bill_line.id)])
                                #     for invoice_line_item in account_invoice_line:
                                #         if invoice_line_item.bl_line_id == cost_profit_line:
                                #             total_qty = total_qty + invoice_line_item.quantity
                                # print('>>>>>>> _onchange_price total qty=' + total_qty)
                                if total_qty > 0:
                                    cost_profit_line.write(
                                        {  # assuming cost_price will always be same for all vendor bills for same item
                                            # 'cost_price': round(price_unit, 2) or 0,
                                            'cost_qty': total_qty or False,
                                            # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                            # 'cost_currency': invoice_line.freight_currency.id,
                                            'invoiced': True,
                                            # 'vendor_id': self.invoice_id.partner_id.id,
                                            # 'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                        })
                                    invoice_line.check_calculate_cost = True
                            else:  # First cost assignment from the vendor bill
                                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                                    if invoice_line.invoice_id.exchange_rate_inverse:
                                        # price_unit = float_round(
                                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                                        #     2,
                                        #     rounding_method='HALF-UP')
                                        price_unit = invoice_line.price_unit
                                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                                        currency_id = invoice_line.invoice_id.currency_id
                                    else:
                                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                                else:
                                    if invoice_line.freight_currency_rate != 1:
                                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                                        price_unit = float_round(
                                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                            2, rounding_method='HALF-UP')
                                    else:
                                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                                 rounding_method='HALF-UP')
                                    freight_currency_rate = invoice_line.freight_currency_rate
                                    currency_id = invoice_line.freight_currency
                                # if self.type == 'in_invoice':
                                # total_cost = total_cost + price_unit
                                # print('>>>>>>> _onchange_price FC price_unit:', price_unit)
                                # total_cost = price_unit   #formula is always cost_price * cost_qty
                                total_qty = invoice_line.quantity
                                cost_profit_line.write({
                                    'cost_price': price_unit,
                                    'cost_qty': total_qty,  # why add 1
                                    'invoiced': True,
                                    'vendor_id': invoice_line.invoice_id.partner_id.id,
                                    'vendor_bill_id': invoice_line.invoice_id.id,
                                    'cost_currency': currency_id.id,
                                    'cost_currency_rate': freight_currency_rate,
                                    # 'vendor_bill_ids': [(4, self.invoice_id.id)],
                                })
                        else:  # First cost assignment from the vendor bill
                            # print('>>>>>>> _onchange_price in_invoice else')
                            if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                                if invoice_line.invoice_id.exchange_rate_inverse:
                                    # price_unit = float_round(
                                    #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                                    #     2, rounding_method='HALF-UP')
                                    price_unit = invoice_line.price_unit
                                    freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                                    currency_id = invoice_line.invoice_id.currency_id
                                else:
                                    raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                            else:
                                if invoice_line.freight_currency_rate != 1:
                                    price_unit = float_round(
                                        invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                        2, rounding_method='HALF-UP')
                                else:
                                    price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                             rounding_method='HALF-UP')
                                freight_currency_rate = invoice_line.freight_currency_rate
                                currency_id = invoice_line.freight_currency
                            cost_profit_line.write({
                                'cost_price': price_unit or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': invoice_line.invoice_id.partner_id.id,
                            })
                elif self.freight_hbl:  # if create vendor bill from job
                    if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                        if invoice_line.invoice_id.exchange_rate_inverse:
                            # price_unit = float_round(
                            #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse,
                            #     2,
                            #     rounding_method='HALF-UP')
                            price_unit = invoice_line.price_unit
                            freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                            currency_id = invoice_line.invoice_id.currency_id
                        else:
                            raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                    else:
                        if invoice_line.freight_currency_rate != 1:
                            # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                            price_unit = float_round(
                                invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                2,
                                rounding_method='HALF-UP')
                        else:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                     rounding_method='HALF-UP')
                        freight_currency_rate = invoice_line.freight_currency_rate
                        currency_id = invoice_line.freight_currency

                    booking = self.env['freight.bol'].browse(self.freight_hbl.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            invoice_line.bl_line_id = cost_profit_line
                            cost_profit_line.write({
                                'cost_price': price_unit or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': self.invoice_id.partner_id.id,
                                # 'vendor_bill_id': self.invoice_id.id,
                                # 'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
                            })
                            break

            elif invoice_line.invoice_id.type == 'out_refund':  # customer credit note
                if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                    if invoice_line.invoice_id.exchange_rate_inverse:
                        # price_unit = float_round(
                        #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse, 2,
                        #     rounding_method='HALF-UP')
                        price_unit = invoice_line.price_unit
                        freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                        currency_id = invoice_line.invoice_id.currency_id
                    else:
                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                else:  # invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(
                            invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                            2, rounding_method='HALF-UP')
                    if invoice_line.freight_currency_rate != 1:
                        price_unit = float_round(
                            invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                            rounding_method='HALF-UP')
                    else:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                 rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                if invoice_line.bl_line_id and len(
                        invoice_line.bl_line_id) > 0:  # Update (if the CN line alrdy in the cost&profit)
                    # print('>>>>>>> _onchange_price bl_line_id >0')
                    cost_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                    cost_line.write({
                        'list_price': -(price_unit),
                        'profit_qty': invoice_line.quantity or False,
                        'profit_currency_rate': freight_currency_rate,
                        'profit_currency': currency_id.id,
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.name,
                    })
                else:
                    if invoice_line.invoice_id and invoice_line.freight_hbl:
                        cost_profit = self.env['freight.bol.cost.profit']
                        sale_line = cost_profit.create({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'profit_qty': invoice_line.quantity,
                            'list_price': -(price_unit),
                            'added_to_invoice': True,
                            'profit_currency_rate': freight_currency_rate,
                            'profit_currency': currency_id.id,
                            'booking_id': invoice_line.freight_hbl.id or False,
                        })
                        invoice_line.bl_line_id = sale_line
                if invoice_line.invoice_id and invoice_line.freight_hbl:
                    booking = self.env['freight.bol'].browse(invoice_line.freight_hbl.id)
                    if not booking.analytic_account_id:
                        # print('>>>> onchange_freight_hbl no analytic account')
                        values = {
                            'code': booking.booking_ref.booking_no,
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.bol_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        # #print('>>>> onchange_freight_hbl with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id,

            elif invoice_line.invoice_id.type == 'in_refund':  # vendor credit note (refund)
                # print('>>>>>>> _onchange_price in_refund')
                booking_id = False
                if invoice_line.invoice_id.freight_hbl:
                    booking_id = invoice_line.invoice_id.freight_hbl.id
                elif invoice_line.freight_hbl:
                    booking_id = invoice_line.freight_hbl.id
                if booking_id:
                    if invoice_line.invoice_id.company_id.currency_id != invoice_line.invoice_id.currency_id:
                        if invoice_line.invoice_id.exchange_rate_inverse:
                            # price_unit = float_round(
                            #     invoice_line.price_subtotal / invoice_line.quantity / invoice_line.invoice_id.exchange_rate_inverse, 2,
                            #     rounding_method='HALF-UP')
                            price_unit = invoice_line.price_unit
                            freight_currency_rate = invoice_line.invoice_id.exchange_rate_inverse
                            currency_id = invoice_line.invoice_id.currency_id
                        else:
                            raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')

                    else:  # invoice is in company currency
                        if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                            invoice_line.price_unit = float_round(
                                invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                                2, rounding_method='HALF-UP')
                        if invoice_line.freight_currency_rate != 1:
                            price_unit = float_round(
                                invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate,
                                2, rounding_method='HALF-UP')
                        else:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                     rounding_method='HALF-UP')
                        freight_currency_rate = invoice_line.freight_currency_rate
                        currency_id = invoice_line.freight_currency
                    if invoice_line.bl_line_id and len(invoice_line.bl_line_id) > 0:
                        # Update (if the CN line alrdy in the cost&profit)
                        # print('>>>>>>> _onchange_price VCN Second time')
                        cost_line = self.env['freight.bol.cost.profit'].browse(invoice_line.bl_line_id.id)
                        cost_line.write({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'cost_price': -(price_unit) or 0,
                            'cost_qty': invoice_line.quantity or False,
                            'cost_currency': currency_id.id,
                            'cost_currency_rate': freight_currency_rate,
                            'invoiced': True,
                            'vendor_id': invoice_line.invoice_id.partner_id.id,
                        })
                    else:
                        # print('>>>>>>> _onchange_price VCN First time')
                        if booking_id:
                            cost_profit = self.env['freight.bol.cost.profit']
                            cost_line = cost_profit.create({
                                'product_id': invoice_line.product_id.id,
                                'product_name': invoice_line.name,
                                'cost_price': -(price_unit) or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': invoice_line.invoice_id.partner_id.id,
                                'booking_id': booking_id or False,
                            })
                            invoice_line.bl_line_id = cost_line
                    booking = self.env['freight.bol'].browse(invoice_line.freight_hbl.id)
                    if not booking.analytic_account_id:
                        # print('>>>> onchange_freight_hbl no analytic account')
                        values = {
                            'code': booking.booking_ref.booking_no,
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.bol_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        # print('>>>> onchange_freight_hbl with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id,

        return res


    @api.multi  # if remove the line items
    def unlink(self):
        for line in self:
            # print('>>>>>>>>>>>>>>>   Invoice Line Unlink')
            if line.bl_line_id:
                cost_line = self.env['freight.bol.cost.profit'].browse(line.bl_line_id.id)
                # print('>>>>>>>>>>>>>>>   cost_line :', self.invoice_type)
                if self.invoice_type == 'in_invoice' and cost_line:  # vendor bill
                    vendor_bill_ids_list = []
                    if cost_line.vendor_bill_ids:
                        total_qty = 0
                        # qty_to_deduct = line.quantity
                        # cost_to_deduct = line.price_unit
                        # total_cost = cost_line.cost_total

                        # total_qty = cost_line.cost_qty
                        # print('>>>>>>>>>>>>>>>   qty_to_deduct :', qty_to_deduct)
                        # print('>>>>>>>>>>>>>>>   total_qty :', total_qty)
                        for vendor_bill in cost_line.vendor_bill_ids:
                            if vendor_bill.id != line.invoice_id.id:
                                vendor_bill_ids_list.append(vendor_bill.id)
                                account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                                                                                 vendor_bill.id)])
                                for invoice_line_item in account_invoice_line:
                                    # print('>>>>>>>>>>  onchange_price_subtotal invoice_line_item.freight_hbl=',
                                    #     invoice_line_item.freight_hbl)
                                    if (invoice_line_item.product_id == cost_line.product_id) and \
                                            (invoice_line_item.freight_hbl.id == cost_line.booking_id.id):
                                        total_qty = total_qty + invoice_line_item.quantity
                                        # print('>>>> onchange_price_subtotal price total_qty=', total_qty)
                        # TS - fix bug where after delete item, not working
                        # total_qty = total_qty - qty_to_deduct
                        # print('>>>>>>>>>>>>>>>   total_qty 2:', total_qty)
                        if len(vendor_bill_ids_list) > 0:  # more than 1 vendor bills
                            cost_line.write(
                                {  # assuming cost_price will always be same for all vendor bills for same item
                                    # 'cost_price': round(price_unit, 2) or 0,
                                    'cost_qty': total_qty or False,
                                    # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                    # 'cost_currency': invoice_line.freight_currency.id,
                                    'invoiced': True,
                                    # 'vendor_id': self.invoice_id.partner_id.id,
                                    'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                })
                        else:  # no more vendor bill
                            # TS - fix bug where after delete item, not working
                            cost_line.write({
                                'cost_price': 0,
                                'cost_qty': 1 or False,
                                'cost_currency_rate': 1.000000,
                                # 'cost_currency': invoice_line.freight_currency.id,
                                'invoiced': False,
                                'paid': False,
                                'vendor_id': False,
                                'vendor_bill_ids': [(5, 0, 0)],  # delete all the items
                                # 'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })
                    # reset from the current line
                    # TS - fix bug where after delete item, not working
                    # line.bl_line_id.unlink()
                    line.bl_line_id.write({
                        'vendor_id_ids': [(3, line.invoice_id.partner_id.id)],
                        'vendor_bill_ids': [(3, line.invoice_id.id)],
                        'invoiced': False,
                        'added_to_invoice': False,
                    })
                    # print(cost_profit)
                elif self.invoice_type == 'out_invoice':
                    if self.freight_hbl:
                        booking = self.env['freight.bol'].browse(self.freight_hbl.id)
                        for cost_profit_line in booking.cost_profit_ids:
                            if cost_profit_line.product_id == line.product_id:
                                cost_profit_line.write({
                                    'list_price': 0,
                                    'profit_qty': 1 or False,
                                    'added_to_invoice': False,
                                })

        return super(GTLAccountInvoiceLine, self).unlink()


    @api.onchange('freight_booking', 'price_subtotal')
    def onchange_freight_booking(self):  # trigger second
        # print('>>>> onchange_price_subtotal 1')
        # vendor bill only
        # print('>>>>>>>>>>> onchange_price_subtotal freight_booking: ', self.invoice_type)
        if self.freight_booking and self.product_id and self.invoice_type == 'in_invoice' and not self.invoice_id.debit_invoice_id:
            booking = self.env['freight.booking'].search([('id', '=', self.freight_booking.id)], limit=1)
            check_booking = False
            # print('>>>>>>>>>>  onchange_price_subtotal 2 booking.id=', booking.id)
            for cost_profit_line in booking.cost_profit_ids:
                # print('>>>>>>>>>>self.product_id', self.product_id, ' , cost_profit_line.product_id=', cost_profit_line.product_id)
                if cost_profit_line.product_id == self.product_id:
                    price_unit = 0
                    freight_currency_rate = 1.000000
                    currency_id = self.freight_currency
                    # print('>>>> onchange_freight_booking equal')
                    # if not cost_profit_line.invoiced:
                    self.booking_line_id = cost_profit_line
                    check_booking = True
                    total_cost = 0
                    total_qty = 0
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        # print('>>>> onchange_price_subtotal price >0')
                        # if already have vendor bills that had assigned cost
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                # print('>>>>>>>>>>  onchange_price_subtotal vendor_bill_ids>1=', len(cost_profit_line.vendor_bill_ids))
                                total_qty = 0
                                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                                                                                     vendor_bill_line.id)])
                                    # print('>>>>>>>>>>  onchange_price_subtotal account_invoice_line=',
                                    #      len(account_invoice_line))
                                    for invoice_line_item in account_invoice_line:
                                        # print('>>>>>>>>>>  onchange_price_subtotal invoice_line_item.freight_booking=',
                                        #     invoice_line_item.freight_booking)
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_booking.id == self.freight_booking.id):
                                            total_qty = total_qty + invoice_line_item.quantity
                                            # print('>>>> onchange_price_subtotal price total_qty=', total_qty)
                                    if not account_invoice_line or len(account_invoice_line) == 0:
                                        total_qty = total_qty + self.quantity
                                if total_qty > 0:
                                    cost_profit_line.write(
                                        {  # assuming cost_price will always be same for all vendor bills for same item
                                            # 'cost_price': round(price_unit, 2) or 0,
                                            'cost_qty': total_qty or False,
                                            # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                            # 'cost_currency': invoice_line.freight_currency.id,
                                            'invoiced': True,
                                            # 'vendor_id': self.invoice_id.partner_id.id,
                                            # 'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                        })
                            else:  # First cost assignment from the vendor bill
                                if self.invoice_id.company_id.currency_id != self.invoice_id.currency_id:
                                    if self.invoice_id.exchange_rate_inverse:
                                        # price_unit = float_round(
                                        #     self.price_subtotal / self.quantity / self.invoice_id.exchange_rate_inverse,
                                        #     2,
                                        #     rounding_method='HALF-UP')
                                        price_unit = self.price_unit
                                        freight_currency_rate = self.invoice_id.exchange_rate_inverse
                                        currency_id = self.invoice_id.currency_id
                                    else:
                                        raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                                else:
                                    if self.freight_currency_rate != 1:
                                        # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                                        price_unit = float_round(
                                            self.price_subtotal / self.quantity / self.freight_currency_rate,
                                            2, rounding_method='HALF-UP')
                                    else:
                                        price_unit = float_round(self.price_subtotal / self.quantity, 2,
                                                                 rounding_method='HALF-UP')
                                    freight_currency_rate = self.freight_currency_rate
                                    currency_id = self.freight_currency
                                # if self.type == 'in_invoice':
                                # total_cost = total_cost + price_unit
                                # print('>>>>>>> _onchange_price freight_booking price_unit:', price_unit)
                                # total_cost = price_unit  # formula is always cost_price * cost_qty
                                total_qty = self.quantity
                                cost_profit_line.write({
                                    'cost_price': price_unit,
                                    'cost_qty': total_qty,  # why add 1
                                    'invoiced': True,
                                    'vendor_id': self.invoice_id.partner_id.id,
                                    'vendor_bill_id': self.invoice_id.id,
                                    'cost_currency': currency_id.id,
                                    'cost_currency_rate': freight_currency_rate,
                                    # 'vendor_bill_ids': [(4, self.invoice_id.id)],
                                })

                        else:
                            # assign the cost for first vendor bill
                            # print('>>>> onchange_price_subtotal else')
                            if self.invoice_id.company_id.currency_id != self.invoice_id.currency_id:
                                if self.invoice_id.exchange_rate_inverse:
                                    # price_unit = float_round(
                                    #     self.price_subtotal / self.quantity / self.invoice_id.exchange_rate_inverse,
                                    #     2,
                                    #     rounding_method='HALF-UP')
                                    price_unit = self.price_unit
                                    freight_currency_rate = self.invoice_id.exchange_rate_inverse
                                    currency_id = self.invoice_id.currency_id
                                else:
                                    raise exceptions.ValidationError('Please Fill in Exchange Rate!!!')
                            else:
                                if self.freight_currency_rate != 1:
                                    # price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                                    price_unit = float_round(
                                        self.price_subtotal / self.quantity / self.freight_currency_rate,
                                        2, rounding_method='HALF-UP')
                                else:
                                    price_unit = float_round(self.price_subtotal / self.quantity, 2,
                                                             rounding_method='HALF-UP')
                                freight_currency_rate = self.freight_currency_rate
                                currency_id = self.freight_currency

                            total_cost = total_cost + price_unit
                            total_qty += self.quantity
                            vendor_ids_list = []
                            # vendor_bill_ids_list = []
                            vendor_ids_list.append(self.invoice_id.partner_id.id)
                            # vendor_bill_ids_list.append(self.invoice_id.id)
                            # print('vendor_ids_list', vendor_ids_list)
                            # print('vendor_ids_list', vendor_bill_ids_list)
                            # print('new_parent_id', self.env.context.get('new_parent_id'))
                            # print('parent_id', self.inv_parent_id)
                            cost_profit_line.write({
                                'cost_price': float_round(total_cost, 2, rounding_method='HALF-UP'),
                                'cost_qty': total_qty,
                                'invoiced': True,
                                'vendor_id': self.invoice_id.partner_id.id,
                                'vendor_bill_id': self.invoice_id.id,
                                'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                # 'vendor_bill_ids': [(4, self.invoice_id._ids)],
                                # 'vendor_bill_ids': [(4, vendor_bill_ids_list)],
                            })

                    if not booking.analytic_account_id:
                        # print('>>>> onchange_freight_booking no analytic account')
                        values = {
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.booking_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        self.account_analytic_id = analytic_account.id
                    else:
                        # print('>>>> onchange_freight_booking with AA')
                        self.account_analytic_id = booking.analytic_account_id.id
            # if check_booking:
            #    booking.action_calculate_cost()
            if not check_booking:
                #print('else not check_booking')
                #TODO - add product
                cost_profit_obj = self.env['freight.cost_profit']
                if self.freight_currency_rate != 1:
                    price_unit = float_round(
                        self.price_subtotal / self.quantity / self.freight_currency_rate,
                        2, rounding_method='HALF-UP')
                else:
                    price_unit = float_round(self.price_subtotal / self.quantity, 2,
                                             rounding_method='HALF-UP')
                cost_profit_line = cost_profit_obj.create({
                    'product_id': self.product_id.id or False,
                    'product_name': self.name or False,
                    'booking_id': booking.id or '',
                    'cost_qty': self.quantity or 0,
                    'cost_currency': self.freight_currency.id,
                    'cost_currency_rate': self.freight_currency_rate or 1.0,
                    'cost_price':  float_round(price_unit, 2, rounding_method='HALF-UP'),
                    'vendor_id':  self.invoice_id.partner_id.id or False,
                    'vendor_bill_id': self.invoice_id.id or 0.0,
                    'invoiced': True,
                })
                booking.write({'cost_profit_ids': cost_profit_line or False})
                if not booking.analytic_account_id:
                    # print('>>>> onchange_freight_booking no analytic account')
                    values = {
                        'partner_id': booking.customer_name.id,
                        'name': '%s' % booking.booking_no,
                        'company_id': self.env.user.company_id.id,
                    }
                    analytic_account = self.env['account.analytic.account'].sudo().create(values)
                    booking.write({'analytic_account_id': analytic_account.id,
                                   })
                    self.account_analytic_id = analytic_account.id
                else:
                    self.account_analytic_id = booking.analytic_account_id.id