from odoo import api, fields, models, exceptions,_
import logging
from datetime import date
from odoo.tools import float_round
_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)


class FreightInvoice(models.Model):
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

    @api.model
    def create(self, vals):
        if vals.get('type') == 'in_refund' or vals.get('type') == 'out_refund' or vals.get('type') == 'in_invoice':
            if self.freight_booking:
                vals.update({'freight_booking': self.freight_booking.id})
        if self.company_id.currency_id != self.currency_id:
            vals.update({'comment': self.env.user.company_id.invoice_note_foreign_currency})
        else:
            vals.update({'comment': self.env.user.company_id.invoice_note})
        res = super(FreightInvoice, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        currency = self.env['res.currency'].browse(vals.get('currency_id'))
        # TS
        if currency:
            for record in self:
                if record.company_id.currency_id != currency:
                    vals.update({'comment': self.env.user.company_id.invoice_note_foreign_currency})
                else:
                    vals.update({'comment': self.env.user.company_id.invoice_note})

        #Refund
        for record in self:
            # if vals.get('state') == 'open':
            #     if record.freight_booking:
            #         booking = self.env['freight.booking'].search([('id', '=', record.freight_booking.id)], limit=1)
            #         booking.action_reupdate_booking_invoice_one()
            #     else:
            #         for invoice_line in record.invoice_line_ids:
            #         sorted_recordset = bookings.sorted(key=lambda r: r.id, reverse=True)
            #TODO
            if vals.get('state') == 'open' and (record.type == 'in_refund' or record.type == 'out_refund'):
                for invoice_line in record.invoice_line_ids:
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
                                invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                                rounding_method='HALF-UP')
                        else:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                                     rounding_method='HALF-UP')
                        freight_currency_rate = invoice_line.freight_currency_rate
                        currency_id = invoice_line.freight_currency
                    if not invoice_line.booking_line_id and invoice_line.invoice_id.freight_booking:
                        #print('>>>>>>> write booking_line_id ==0')
                        cost_profit = self.env['freight.cost_profit']

                        if record.type == 'out_refund' and invoice_line.invoice_id.freight_booking:
                            sale_line = cost_profit.create({
                                'product_id': invoice_line.product_id.id,
                                'product_name': invoice_line.name,
                                'profit_qty': invoice_line.quantity,
                                'list_price': -(price_unit),
                                'added_to_invoice': True,
                                'profit_currency_rate': freight_currency_rate,
                                'profit_currency': currency_id.id,
                                'booking_id': invoice_line.invoice_id.freight_booking.id or False,
                            })
                            invoice_line.booking_line_id = sale_line
                        elif record.type == 'in_refund':
                            booking_id = False
                            if invoice_line.invoice_id.freight_booking:
                                booking_id = invoice_line.invoice_id.freight_booking.id
                            elif invoice_line.freight_booking:
                                booking_id = invoice_line.freight_booking.id
                            if booking_id:
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
                                invoice_line.booking_line_id = cost_line
                    if invoice_line.invoice_id.freight_booking:
                        booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
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
                            invoice_line.account_analytic_id = analytic_account.id,
                        else:
                            # print('>>>> onchange_freight_booking with AA')
                            invoice_line.account_analytic_id = booking.analytic_account_id.id
            # if vals.get('state') == 'open' and record.state == 'draft' and record.type == 'in_refund':
            #     invoice_lines = self.env['account.invoice.line'].search([('invoice_id', '=', record.id)])
            #     for invoice_line in invoice_lines:
            #         if invoice_line.booking_line_id:
            #             line = {
            #                 'vendor_bill_ids': [(4, record.id)],
            #             }
            #             invoice_line.booking_line_id.write(line)
            #             if invoice_line.freight_booking:
            #                 booking = self.env['freight.booking'].search([('id', '=', invoice_line.freight_booking.id)], limit=1)
            #                 #booking.action_calculate_cost()

            #Cancel Vendor Bill
            # if vals.get('state') == 'cancel' and (record.type == 'in_invoice' or record.type == 'in_refund'):
            #     for invoice_line in record.invoice_line_ids:
            #         if invoice_line.booking_line_id:
            #             cost_profit = self.env['freight.cost_profit'].search(
            #                 [('id', '=', invoice_line.booking_line_id.id)], limit=1)
            #             if record.type == 'in_invoice':
            #                 cost_profit.write({
            #                     'vendor_id_ids': [(3, record.partner_id.id)],
            #                     'vendor_bill_ids': [(3, record.id)],
            #                     'invoiced': False,
            #                 })
            #             if record.type == 'in_refund':
            #                 cost_profit.write({
            #                     'vendor_bill_ids': [(3, record.id)],
            #                 })
            #             booking = self.env['freight.booking'].search([('id', '=', cost_profit.booking_id.id)], limit=1)
                        #booking.action_calculate_cost()
        res = super(FreightInvoice, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        #print("Invoice Unlink")
        for inv in self:
            for invoice_line in inv.invoice_line_ids:
                if invoice_line.booking_line_id:
                    cost_profit_line = self.env['freight.cost_profit'].search([('id', '=', invoice_line.booking_line_id.id)],
                                                                         limit=1)
                    if self.type == 'in_invoice':  #when delete a vendor bill item
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
                                                (invoice_line_item.freight_booking.id == invoice_line.freight_booking.id):
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
                                        'invoiced': True,
                                        # 'vendor_id': self.invoice_id.partner_id.id,
                                        'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                    })
                            # cost_profit.write({
                            #     'vendor_id_ids': [(3, self.partner_id.id)],
                            #     'vendor_bill_ids': [(3, self.id)],
                            #     'invoiced': False,
                            # })
                        else: #if only 1 vendor bill
                            cost_profit_line.write({
                                'vendor_id': False,
                                'vendor_bill_ids': [(3, self.id)],
                                'invoiced': False,
                                'cost_price': 0,
                                'cost_qty': 0,
                                'cost_currency_rate': 1.000000,
                                'cost_currency': False,
                            })
                # if self.type == 'in_refund':
                    #     cost_profit.write({
                    #         'vendor_bill_ids': [(3, self.id)],
                    #     })
                    #booking = self.env['freight.booking'].search([('id', '=', cost_profit.booking_id.id)], limit=1)
                    #booking.action_calculate_cost()
            return super(FreightInvoice, self).unlink()


    @api.onchange('date_invoice')
    def onchange_date_invoice(self):
        if not self.invoice_note:
            self.invoice_note = self.env.user.company_id.invoice_note


    @api.multi
    def _get_use_invoice_note(self):
        for record in self:
            # TS
            if record.company_id.currency_id != record.currency_id:
                record.invoice_note = self.env.user.company_id.invoice_note_foreign_currency
            else:
                record.invoice_note = self.env.user.company_id.invoice_note

    # TS - bug fix the CN/Invoice not updating the comment
    @api.onchange('currency_id')
    def onchange_currency_id(self):
        if self.currency_id:
            if self.company_id.currency_id != self.currency_id:
                self.comment = self.env.user.company_id.invoice_note_foreign_currency


    @api.onchange('exchange_rate_inverse')
    def _onchange_price(self):
        for invoice_line in self.invoice_line_ids:
            invoice_line.onchange_price_unit()


    #main purpose is to update the vendor_bill_ids in the cost&profit items
    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        #print('super _onchange_invoice_line_ids')
        filtered_invoice_lines = self.invoice_line_ids.filtered(lambda r: not r.check_calculate_cost)
        for invoice_line in filtered_invoice_lines:
            is_first = False
            #('>>>>>>>>>>> onchange_invoice_line_ids=' + invoice_line.invoice_type)
            if invoice_line.booking_line_id and (invoice_line.invoice_type == 'in_invoice'
                                                 or invoice_line.invoice_type == 'in_refund') and not invoice_line.check_calculate_cost:
                #print('>>>>>>>>>>> onchange_invoice_line_ids booking_line_id')
                if invoice_line.freight_booking:
                    #print('>>>>>>>>>>> onchange_invoice_line_ids freight booking')
                #if invoice_line.freight_booking and not invoice_line.check_calculate_cost:
                    cost_profit = self.env['freight.cost_profit'].search([('id', '=', invoice_line.booking_line_id.id)],
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
                            #TS - fix bug (Analytic Account is false when VCN is created) TODO
                            if not invoice_line.freight_booking.analytic_account_id:
                                # print('>>>> onchange_freight_booking no analytic account')
                                values = {
                                    'partner_id': invoice_line.freight_booking.customer_name.id,
                                    'name': '%s' % invoice_line.freight_booking.booking_no,
                                    'company_id': self.env.user.company_id.id,
                                }
                                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                                invoice_line.freight_booking.write({'analytic_account_id': analytic_account.id,
                                               })
                                #TS bug fixed - sometimes account analytic not assigned
                                invoice_line.write({'account_analytic_id': analytic_account.id,})
                                #invoice_line.account_analytic_id = analytic_account.id,
                            else:
                                # print('>>>> onchange_freight_booking with AA')
                                invoice_line.account_analytic_id = invoice_line.freight_booking.analytic_account_id.id
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
        purchase_ids = self.invoice_line_ids.mapped('purchase_id')
        if purchase_ids:
            self.origin = ', '.join(purchase_ids.mapped('name'))
        #TS - this is important to recalculate the Tax, if there is any change to qty, price, etc
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines
    # @api.onchange('invoice_line_ids')
    # def _onchange_invoice_line_ids(self):
    #     for invoice_line in self.invoice_line_ids:
    #         #print(invoice_line)
    #         #print(invoice_line.check_calculate_cost)
    #         if invoice_line.booking_line_id and invoice_line.invoice_type == 'in_invoice':
    #             if invoice_line.freight_booking and not invoice_line.check_calculate_cost:
    #                 print("Update Booking")
    #                 booking = self.env['freight.booking'].search([('id', '=', invoice_line.freight_booking.id)], limit=1)
    #                 cost_profit = self.env['freight.cost_profit'].search([('id', '=', invoice_line.booking_line_id.id)], limit=1)
    #
    #                 if not booking.analytic_account_id:
    #                     values = {
    #                         'partner_id': booking.customer_name.id,
    #                         'name': '%s' % booking.booking_no,
    #                         'company_id': self.env.user.company_id.id,
    #                     }
    #                     analytic_account = self.env['account.analytic.account'].sudo().create(values)
    #                     booking.write({'analytic_account_id': analytic_account.id,
    #                                    })
    #
    #                 self.freight_booking = booking.id,
    #                 self.account_analytic_id = booking.analytic_account_id.id,
    #                 invoice_line.account_analytic_id = booking.analytic_account_id.id,
    #
    #                 vendor_ids_list = []
    #                 vendor_bill_ids_list = []
    #                 total_price = 0
    #                 total_qty = 0
    #
    #                 for cost_profit_vendor_list in cost_profit.vendor_id_ids:
    #                     vendor_ids_list.append(cost_profit_vendor_list.id)
    #
    #                 for cost_profit_vendor_bill_list in cost_profit.vendor_bill_ids:
    #                     vendor_bill_ids_list.append(cost_profit_vendor_bill_list.id)
    #
    #
    #                 vendor_bill_ids_list.append(self._origin.id)
    #                 vendor_ids_list.append(self.partner_id.id)
    #                 if self._origin.id:
    #                     cost_profit.write({
    #                         'vendor_id_ids': [(6, 0, vendor_ids_list)],
    #                         'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
    #                     })
    #
    #                 cost_profit.write({
    #                     'invoiced': True,
    #                     'vendor_id': self.partner_id.id,
    #                     'vendor_bill_id': self._origin.id,
    #                     #'cost_amount': invoice_line.price_subtotal,
    #                     #'cost_price': invoice_line.price_unit,
    #                     #'cost_qty': invoice_line.quantity,
    #                 })
    #                 booking.action_calculate_cost()
    #                 invoice_line.write({
    #                     'check_calculate_cost': True,
    #                     #'freight_booking': invoice_line.freight_booking.id,
    #                     #'booking_line_id': invoice_line.booking_line_id.id,
    #                 })
    #
    #     purchase_ids = self.invoice_line_ids.mapped('purchase_id')
    #     if purchase_ids:
    #         self.origin = ', '.join(purchase_ids.mapped('name'))
    #
    #
    #     taxes_grouped = self.get_taxes_values()
    #     tax_lines = self.tax_line_ids.filtered('manual')
    #     for tax in taxes_grouped.values():
    #         tax_lines += tax_lines.new(tax)
    #     self.tax_line_ids = tax_lines
    #     return

    def action_assign_job_cost(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_invoice.job_cost_wizard_form')
        return {
            'name': 'Assign Job Cost',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'job.cost.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(self.env.context,
                            vendor_bill_id=self.id,
                            partner_id=self.partner_id.id,
                            ),
        }


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    # booking_job_cost = fields.Many2one('freight.cost_profit', string='Job Cost')
    freight_booking = fields.Many2one('freight.booking', string='Booking Job', copy=False)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=False)
    lorry_type = fields.Char('Lorry Type')
    lorry_no = fields.Char('Lorry No')
    location = fields.Char('Pickup From')
    dest_location = fields.Char('Deliver To')
    do_no = fields.Char('DO No')
    check_calculate_cost = fields.Boolean('Check Calculate Cost')

    booking_line_id = fields.Many2one('freight.cost_profit', copy=False)
    bl_line_id = fields.Many2one('freight.bol.cost.profit', copy=False)
    #inv_parent_id = fields.Integer(string='parent_id', copy=False, compute="_compute_inv_parent_id")

    # def _compute_inv_parent_id(self):
    #     print('_compute_inv_parent_id');
    #     for operation in self:
    #         operation.inv_parent_id = self.env.context.get('new_parent_id')

    @api.model
    def create(self, vals):
        #To fix - by default Vendor DN/Vendor CN will copy the line info from the parent
        invoice_line = super(AccountInvoiceLine, self).create(vals)
        if invoice_line.invoice_id.type == 'in_refund':
            invoice_line.booking_line_id = False
        elif invoice_line.invoice_id.type == 'in_invoice' and \
                invoice_line.invoice_id.debit_invoice_id:
            invoice_line.booking_line_id = False
        elif invoice_line.invoice_id.type == 'out_refund':
            invoice_line.booking_line_id = False
        return invoice_line


    def action_assign_job_cost(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_invoice.view_job_cost_form')
        return {
            'name': 'Add Job Cost',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.booking.job.cost',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(self.env.context,
                            vendor_bill_id=self.invoice_id.id,
                            partner_id=self.partner_id.id,
                            product_id=self.product_id.id,
                            ),
            # 'res_id': self.id,
        }

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type

        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner.'),
            }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            self_lang = self
            if part.lang:
                self_lang = self.with_context(lang=part.lang)

            product = self_lang.product_id
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            product_name = self_lang._get_invoice_line_name_from_product()
            if not self.name:
                self.name = self.product_id.name

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}



    @api.onchange('freight_booking', 'price_subtotal')
    def onchange_freight_booking(self):   #trigger second
        #print('>>>> onchange_price_subtotal 1')
        #vendor bill only
        #print('>>>>>>>>>>> onchange_price_subtotal freight_booking: ', self.invoice_type)
        if self.freight_booking and self.product_id and self.invoice_type == 'in_invoice' and not self.invoice_id.debit_invoice_id:
            booking = self.env['freight.booking'].search([('id', '=', self.freight_booking.id)], limit=1)
            check_booking = False
            #print('>>>>>>>>>>  onchange_price_subtotal 2 booking.id=', booking.id)
            for cost_profit_line in booking.cost_profit_ids:
                #print('>>>>>>>>>>self.product_id', self.product_id, ' , cost_profit_line.product_id=', cost_profit_line.product_id)
                if cost_profit_line.product_id == self.product_id:
                    price_unit = 0
                    freight_currency_rate = 1.000000
                    currency_id = self.freight_currency
                    #print('>>>> onchange_freight_booking equal')
                    #if not cost_profit_line.invoiced:
                    self.booking_line_id = cost_profit_line
                    check_booking = True
                    total_cost = 0
                    total_qty = 0
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        #print('>>>> onchange_price_subtotal price >0')
                        # if already have vendor bills that had assigned cost
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                #print('>>>>>>>>>>  onchange_price_subtotal vendor_bill_ids>1=', len(cost_profit_line.vendor_bill_ids))
                                total_qty = 0
                                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                                                                                     vendor_bill_line.id)])
                                    #print('>>>>>>>>>>  onchange_price_subtotal account_invoice_line=',
                                    #      len(account_invoice_line))
                                    for invoice_line_item in account_invoice_line:
                                        #print('>>>>>>>>>>  onchange_price_subtotal invoice_line_item.freight_booking=',
                                         #     invoice_line_item.freight_booking)
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_booking.id == self.freight_booking.id):
                                            total_qty = total_qty + invoice_line_item.quantity
                                            #print('>>>> onchange_price_subtotal price total_qty=', total_qty)
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
                                #print('>>>>>>> _onchange_price freight_booking price_unit:', price_unit)
                                #total_cost = price_unit  # formula is always cost_price * cost_qty
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
                            #assign the cost for first vendor bill
                            #print('>>>> onchange_price_subtotal else')
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

                            #print('>>>> onchange_freight_booking price_unit=', str(price_unit))
                                #price_unit = invoice_line_item.price_subtotal / self.quantity
                            total_cost = total_cost + price_unit
                            total_qty += self.quantity
                            vendor_ids_list = []
                           #vendor_bill_ids_list = []
                            vendor_ids_list.append(self.invoice_id.partner_id.id)
                            #vendor_bill_ids_list.append(self.invoice_id.id)
                            #print('vendor_ids_list', vendor_ids_list)
                            #print('vendor_ids_list', vendor_bill_ids_list)
                            #print('new_parent_id', self.env.context.get('new_parent_id'))
                            #print('parent_id', self.inv_parent_id)
                            cost_profit_line.write({
                                'cost_price': float_round(total_cost, 2, rounding_method='HALF-UP'),
                                'cost_qty': total_qty,
                                'invoiced': True,
                                'vendor_id': self.invoice_id.partner_id.id,
                                'vendor_bill_id': self.invoice_id.id,
                                'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                #'vendor_bill_ids': [(4, self.invoice_id._ids)],
                                #'vendor_bill_ids': [(4, vendor_bill_ids_list)],
                            })


                    if not booking.analytic_account_id:
                        #print('>>>> onchange_freight_booking no analytic account')
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
                        #print('>>>> onchange_freight_booking with AA')
                        self.account_analytic_id = booking.analytic_account_id.id
            #if check_booking:
            #    booking.action_calculate_cost()
            if not check_booking:
                raise exceptions.ValidationError('Product Not Found in Booking Job Cost&Profit')

        # if self.invoice_id:
        #     raise exceptions.ValidationError('Please Save the Invoice/Vendor Bill First and Proceed invoice_id!!!')
        # if self.invoice_id.type:
        #     raise exceptions.ValidationError('Please Save the Invoice/Vendor Bill First and Proceed type!!!')


    @api.onchange('price_unit')
    def onchange_price_unit(self):
        #print('super onchange_price_unit')
        for invoice_line in self:
            price_unit = 0
            freight_currency_rate = 1.000000
            currency_id = invoice_line.freight_currency
            #print('>>>>>>> _onchange_price_unit type=', invoice_line.invoice_id.type)
            #print('>>>>>>> _onchange_price_unit customer_debit_note=', invoice_line.invoice_id.customer_debit_note)
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
                        #print('>>>>>>>super  _onchange_price INVOICE')
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
                    #print('>>>>>>> _onchange_price price_unit 2:', price_unit)
                if invoice_line.invoice_id.freight_booking:
                    #print('>>>>>>> super _onchange_price booking')
                    booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            #print('>>>>>>> super _onchange_price product=', invoice_line.product_id.name)
                            cost_profit_line.write({
                                'list_price': price_unit,
                                'profit_qty': invoice_line.quantity or False,
                                'profit_currency_rate': freight_currency_rate,
                                'profit_currency': currency_id.id,
                            })
                            break

            elif invoice_line.invoice_id.type == 'in_invoice' and \
                    invoice_line.invoice_id.debit_invoice_id:  # vendor debit note
                #print('>>>>>>> _onchange_price_unit VDN')
                if invoice_line.invoice_id.freight_booking:
                    booking_id = invoice_line.invoice_id.freight_booking.id
                elif invoice_line.freight_booking:
                    booking_id = invoice_line.freight_booking.id

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
                    #print('>>>>>>> _onchange_price_unit VDN price_unit ', price_unit)
                    # Update (if the DN line alrdy in the cost&profit)
                if invoice_line.booking_line_id and len(invoice_line.booking_line_id) > 0:
                    #print('>>>>>>> _onchange_price VCN Second time')
                    cost_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
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
                    #print('>>>>>>> _onchange_price VDN First time')
                    if booking_id:
                        cost_profit = self.env['freight.cost_profit']
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
                        invoice_line.booking_line_id = cost_line
                booking = self.env['freight.booking'].browse(booking_id)
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
                    invoice_line.account_analytic_id = analytic_account.id,
                else:
                    # print('>>>> onchange_freight_booking with AA')
                    invoice_line.account_analytic_id = booking.analytic_account_id.id

            elif invoice_line.invoice_id.type == 'in_invoice':  # vendor bill
                # if vendor bill is created directly and assigned job line by line or when update qty/FC/price unit
                #print('>>>>>>> _onchange_price_unit in_invoice')
                if invoice_line.booking_line_id and not (
                        invoice_line.invoice_type == 'in_refund' or invoice_line.invoice_type == 'out_refund'):
                    cost_profit_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                #print('>>>>>>> _onchange_price_unit in_invoice > 1')
                                total_qty = 0
                                for vendor_bill_id in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search(
                                        [('invoice_id', '=', vendor_bill_id.id)])
                                    for invoice_line_item in account_invoice_line:
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_booking.id == self.freight_booking.id):
                                        #if invoice_line_item.product_id == cost_profit_line.product_id:
                                            total_qty = total_qty + invoice_line_item.quantity
                                            # account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                            #     vendor_bill_line.id)])
                                            #     for invoice_line_item in account_invoice_line:
                                            #         if invoice_line_item.booking_line_id == cost_profit_line:
                                            #             total_qty = total_qty + invoice_line_item.quantity
                                            #print('>>>>>>> _onchange_price_unit total qty=' + total_qty)
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
                                #print('>>>>>>> _onchange_price_unit 222')
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
                                #     #if invoice_line_item.booking_line_id == cost_profit_line:
                                #     total_cost = cost_profit_line.cost_total
                                #     #price_unit = invoice_line_item.price_subtotal / invoice_line_item.quantity
                                #     total_cost = total_cost + self.price_subtotal
                                #     #total_qty = total_qty - invoice_line_item.quantity
                                #     cost_profit_line.write({
                                #         'cost_total': round(total_cost, 2),
                                #     })
                        else:  # First cost assignment from the vendor bill
                            #print('>>>>>>> _onchange_price_unit in_invoice else')
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
                elif self.invoice_id.freight_booking:  # if create vendor bill from job
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

                    booking = self.env['freight.booking'].browse(self.invoice_id.freight_booking.id)
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

                if invoice_line.booking_line_id and len(invoice_line.booking_line_id) > 0:  # Update (if the CN line alrdy in the cost&profit)
                    #print('>>>>>>> _onchange_price_unit booking_line_id >0')
                    cost_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
                    cost_line.write({
                        'list_price': -(price_unit),
                        'profit_qty': invoice_line.quantity or False,
                        'profit_currency_rate': freight_currency_rate,
                        'profit_currency': currency_id.id,
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.name,
                    })
                else:
                    if invoice_line.invoice_id and invoice_line.invoice_id.freight_booking:
                    #print('>>>>>>> _onchange_price_unit booking_line_id ==0')
                        cost_profit = self.env['freight.cost_profit']
                        sale_line = cost_profit.create({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'profit_qty': invoice_line.quantity,
                            'list_price': -(price_unit),
                            'added_to_invoice': True,
                            'profit_currency_rate': freight_currency_rate,
                            'profit_currency': currency_id.id,
                            'booking_id': invoice_line.invoice_id.freight_booking.id or False,
                        })
                        invoice_line.booking_line_id = sale_line

                if invoice_line.invoice_id and invoice_line.invoice_id.freight_booking:
                    booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
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
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        # print('>>>> onchange_freight_booking with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id,

            elif invoice_line.invoice_id.type == 'in_refund':  # vendor credit note (refund)
                #print('>>>>>>> _onchange_price_unit VCN')
                booking_id = False
                if invoice_line.invoice_id.freight_booking:
                    booking_id = invoice_line.invoice_id.freight_booking.id
                elif invoice_line.freight_booking:
                    booking_id = invoice_line.freight_booking.id
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
                    #print('>>>>>>> _onchange_price_unit VCN price_unit ', price_unit)
                    # Update (if the CN line alrdy in the cost&profit)
                if booking_id:
                    if invoice_line.booking_line_id and len(invoice_line.booking_line_id) > 0:
                        #print('>>>>>>> _onchange_price VCN Second time')
                        cost_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
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
                        #print('>>>>>>> _onchange_price VCN First time')
                        if booking_id:
                            cost_profit = self.env['freight.cost_profit']
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
                            invoice_line.booking_line_id = cost_line
                    booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
                    if booking and not booking.analytic_account_id:
                        # print('>>>> onchange_freight_booking no analytic account')
                        values = {
                            'partner_id': booking.customer_name.id,
                            'name': '%s' % booking.booking_no,
                            'company_id': self.env.user.company_id.id,
                        }
                        analytic_account = self.env['account.analytic.account'].sudo().create(values)
                        booking.write({'analytic_account_id': analytic_account.id,
                                       })
                        invoice_line.account_analytic_id = analytic_account.id
                    elif booking and booking.analytic_account_id:
                        # print('>>>> onchange_freight_booking with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id


    @api.onchange('freight_foreign_price', 'quantity', 'freight_currency_rate')
    def _onchange_price(self):   #trigger first
        #print('>>>>> super onchange_price')
        #print('>>>>>>> _onchange_price FC rate=', self.freight_currency_rate)
        #print('>>>>>>> _onchange_price FF price=', self.freight_foreign_price)
        #print('>>>>>>> _onchange_price rounded=', round(self.freight_currency_rate * self.freight_foreign_price, 2))
        #print('>>>>>>> _onchange_price price unit=', self.price_unit)
        for invoice_line in self:
            price_unit = 0
            freight_currency_rate = 1.000000
            currency_id = invoice_line.freight_currency
            #print('>>>>>>> _onchange_price customer_debit_note=', invoice_line.invoice_id.customer_debit_note)
            #print('>>>>>>> _onchange_price debit_invoice_id=', invoice_line.invoice_id.debit_invoice_id)
            if invoice_line.invoice_id.type == 'out_invoice':  #invoice
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

                else:   #invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                                                      2, rounding_method='HALF-UP')
                    #print('>>>>>>> _onchange_price INVOICE')
                    #list_price = invoice_line.freight_foreign_price / invoice_line.freight_currency_rate
                    if invoice_line.freight_currency_rate != 1:
                        #price_unit = invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2, rounding_method='HALF-UP')
                        #print('>>>>>>> _onchange_price price_unit 1:', price_unit)
                    else:
                        #price_unit = invoice_line.price_subtotal / invoice_line.quantity
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2, rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                #print('>>>>>>> _onchange_price price_unit 2:', price_unit)
                if invoice_line.invoice_id.freight_booking:
                    #print('>>>>>>> _onchange_price booking')
                    booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            #print('>>>>>>> _onchange_price product=', invoice_line.product_id.name)
                            cost_profit_line.write({
                                'list_price': price_unit,
                                'profit_qty': invoice_line.quantity or False,
                                'profit_currency_rate': freight_currency_rate,
                                'profit_currency': currency_id.id,
                            })
                            break

            elif invoice_line.invoice_id.type == 'in_invoice' and \
                invoice_line.invoice_id.debit_invoice_id:  # vendor debit note
                #print('>>>>>>> _onchange_price_unit VDN')
                if invoice_line.invoice_id.freight_booking:
                    booking_id = invoice_line.invoice_id.freight_booking.id
                elif invoice_line.freight_booking:
                    booking_id = invoice_line.freight_booking.id

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
                    #print('>>>>>>> _onchange_price_unit VDN price_unit ', price_unit)
                # Update (if the DN line alrdy in the cost&profit)
                if invoice_line.booking_line_id and len(invoice_line.booking_line_id) > 0:
                    #print('>>>>>>> _onchange_price VCN Second time')
                    cost_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
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
                    #print('>>>>>>> _onchange_price VDN First time')
                    if booking_id:
                        cost_profit = self.env['freight.cost_profit']
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
                        invoice_line.booking_line_id = cost_line
                booking = self.env['freight.booking'].browse(booking_id)
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
                    invoice_line.account_analytic_id = analytic_account.id,
                else:
                    # print('>>>> onchange_freight_booking with AA')
                    invoice_line.account_analytic_id = booking.analytic_account_id.id,
            elif invoice_line.invoice_id.type == 'in_invoice':  #vendor bill
                #if vendor bill is created directly and assigned job line by line or when update qty/FC/price unit
                #print('>>>>>>> _onchange_price in vendor bill')
                if invoice_line.booking_line_id and not (
                        invoice_line.invoice_type == 'in_refund' or invoice_line.invoice_type == 'out_refund'):
                    cost_profit_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                                                      2, rounding_method='HALF-UP')
                    #print('>>>>>>> _onchange_price in_invoice price_unit')
                    if self.price_subtotal and (self.price_subtotal > 0 or self.price_subtotal < 0):
                        if cost_profit_line.vendor_bill_ids:
                            # for second/third vendor bill to the same job cost
                            if len(cost_profit_line.vendor_bill_ids) > 1:
                                #print('>>>>>>> _onchange_price in_invoice > 1')
                                total_qty = 0
                                for vendor_bill_id in cost_profit_line.vendor_bill_ids:
                                    account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                        vendor_bill_id.id)])
                                    for invoice_line_item in account_invoice_line:
                                        if (invoice_line_item.product_id == cost_profit_line.product_id) and \
                                                (invoice_line_item.freight_booking.id == self.freight_booking.id):
                                        #if invoice_line_item.product_id == cost_profit_line.product_id:
                                            total_qty = total_qty + invoice_line_item.quantity
                                    if not account_invoice_line or len(account_invoice_line) == 0:
                                        total_qty = total_qty + self.quantity
                                     # account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                     #     vendor_bill_line.id)])
                                #     for invoice_line_item in account_invoice_line:
                                #         if invoice_line_item.booking_line_id == cost_profit_line:
                                #             total_qty = total_qty + invoice_line_item.quantity
                                            #print('>>>>>>> _onchange_price total qty=' + total_qty)
                                if total_qty > 0:
                                    cost_profit_line.write(
                                        {  # assuming cost_price will always be same for all vendor bills for same item
                                            # 'cost_price': round(price_unit, 2) or 0,
                                            'cost_qty': total_qty or False,
                                            # 'cost_currency_rate': invoice_line.freight_currency_rate,
                                            # 'cost_currency': invoice_line.freight_currency.id,
                                            'invoiced': True,
                                            # 'vendor_id': self.invoice_id.partner_id.id,
                                            #'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                                        })
                                    invoice_line.check_calculate_cost = True
                            else:  #First cost assignment from the vendor bill
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
                                #if self.type == 'in_invoice':
                                    #total_cost = total_cost + price_unit
                                #print('>>>>>>> _onchange_price FC price_unit:', price_unit)
                                #total_cost = price_unit   #formula is always cost_price * cost_qty
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
                                #     #if invoice_line_item.booking_line_id == cost_profit_line:
                                #     total_cost = cost_profit_line.cost_total
                                #     #price_unit = invoice_line_item.price_subtotal / invoice_line_item.quantity
                                #     total_cost = total_cost + self.price_subtotal
                                #     #total_qty = total_qty - invoice_line_item.quantity
                                #     cost_profit_line.write({
                                #         'cost_total': round(total_cost, 2),
                                #     })
                        else:  #First cost assignment from the vendor bill
                            #print('>>>>>>> _onchange_price in_invoice else')
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
                elif self.invoice_id.freight_booking:  #if create vendor bill from job
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
                                invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2,
                                rounding_method='HALF-UP')
                        else:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2,
                                               rounding_method='HALF-UP')
                        freight_currency_rate = invoice_line.freight_currency_rate
                        currency_id = invoice_line.freight_currency

                    booking = self.env['freight.booking'].browse(self.invoice_id.freight_booking.id)
                    for cost_profit_line in booking.cost_profit_ids:
                        if cost_profit_line.product_id == invoice_line.product_id:
                            invoice_line.booking_line_id = cost_profit_line
                            cost_profit_line.write({
                                'cost_price': price_unit or 0,
                                'cost_qty': invoice_line.quantity or False,
                                'cost_currency': currency_id.id,
                                'cost_currency_rate': freight_currency_rate,
                                'invoiced': True,
                                'vendor_id': self.invoice_id.partner_id.id,
                                #'vendor_bill_id': self.invoice_id.id,
                                #'vendor_id_ids': [(4, self.invoice_id.partner_id.id)],
                            })
                            break

            elif invoice_line.invoice_id.type == 'out_refund':  #customer credit note
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

                else:   #invoice is in company currency
                    if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                        invoice_line.price_unit = float_round(invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                                                      2, rounding_method='HALF-UP')
                    if invoice_line.freight_currency_rate != 1:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2, rounding_method='HALF-UP')
                    else:
                        price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2, rounding_method='HALF-UP')
                    freight_currency_rate = invoice_line.freight_currency_rate
                    currency_id = invoice_line.freight_currency
                if invoice_line.booking_line_id and len(invoice_line.booking_line_id)>0:   #Update (if the CN line alrdy in the cost&profit)
                    #print('>>>>>>> _onchange_price booking_line_id >0')
                    cost_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
                    cost_line.write({
                        'list_price': -(price_unit),
                        'profit_qty': invoice_line.quantity or False,
                        'profit_currency_rate': freight_currency_rate,
                        'profit_currency': currency_id.id,
                        'product_id': invoice_line.product_id.id,
                        'product_name': invoice_line.name,
                    })
                else:
                    if invoice_line.invoice_id and invoice_line.invoice_id.freight_booking:
                        cost_profit = self.env['freight.cost_profit']
                        sale_line = cost_profit.create({
                            'product_id': invoice_line.product_id.id,
                            'product_name': invoice_line.name,
                            'profit_qty': invoice_line.quantity,
                            'list_price': -(price_unit),
                            'added_to_invoice': True,
                            'profit_currency_rate': freight_currency_rate,
                            'profit_currency': currency_id.id,
                            'booking_id': invoice_line.invoice_id.freight_booking.id or False,
                        })
                        invoice_line.booking_line_id = sale_line
                if invoice_line.invoice_id and invoice_line.invoice_id.freight_booking:
                    booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
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
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        # #print('>>>> onchange_freight_booking with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id,

            elif invoice_line.invoice_id.type == 'in_refund':  #vendor credit note (refund)
                #print('>>>>>>> _onchange_price in_refund')
                booking_id = False
                if invoice_line.invoice_id.freight_booking:
                    booking_id = invoice_line.invoice_id.freight_booking.id
                elif invoice_line.freight_booking:
                    booking_id = invoice_line.freight_booking.id
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

                    else:   #invoice is in company currency
                        if invoice_line.quantity and invoice_line.freight_currency_rate and invoice_line.freight_foreign_price:
                            invoice_line.price_unit = float_round(invoice_line.freight_currency_rate * invoice_line.freight_foreign_price,
                                                          2, rounding_method='HALF-UP')
                        if invoice_line.freight_currency_rate != 1:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity / invoice_line.freight_currency_rate, 2, rounding_method='HALF-UP')
                        else:
                            price_unit = float_round(invoice_line.price_subtotal / invoice_line.quantity, 2, rounding_method='HALF-UP')
                        freight_currency_rate = invoice_line.freight_currency_rate
                        currency_id = invoice_line.freight_currency
                    if invoice_line.booking_line_id and len(invoice_line.booking_line_id) > 0:
                        #Update (if the CN line alrdy in the cost&profit)
                        #print('>>>>>>> _onchange_price VCN Second time')
                        cost_line = self.env['freight.cost_profit'].browse(invoice_line.booking_line_id.id)
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
                        #print('>>>>>>> _onchange_price VCN First time')
                        if booking_id:
                            cost_profit = self.env['freight.cost_profit']
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
                            invoice_line.booking_line_id = cost_line
                    booking = self.env['freight.booking'].browse(invoice_line.invoice_id.freight_booking.id)
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
                        invoice_line.account_analytic_id = analytic_account.id,
                    else:
                        # print('>>>> onchange_freight_booking with AA')
                        invoice_line.account_analytic_id = booking.analytic_account_id.id,


    # @api.onchange('price_subtotal')
    # def onchange_price_subtotal(self):
    #     if self.invoice_id and self.freight_booking and self.product_id:
    #         booking = self.env['freight.booking'].search([('id', '=', self.freight_booking.id)], limit=1)
    #         check_booking = False
    #         for cost_profit_line in booking.cost_profit_ids:
    #             if cost_profit_line.product_id == self.product_id:
    #                 # if not cost_profit_line.invoiced:
    #                 self.booking_line_id = cost_profit_line
    #                 check_booking = True
    #                 total_cost = 0
    #                 total_qty = 0
    #                 # if already have vendor bills that had assigned cost
    #                 if self.price_subtotal and self.price_subtotal > 0:
    #                     if cost_profit_line.vendor_bill_ids:
    #                         for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                             account_invoice_line = self.env['account.invoice.line'].search(
    #                                 [('invoice_id', '=', vendor_bill_line.id)])
    #                             if account_invoice_line:
    #                                 for invoice_line_item in account_invoice_line:
    #                                     if invoice_line_item.booking_line_id == cost_profit_line:
    #                                         if invoice_line_item.freight_currency_rate != 1:
    #                                             price_unit = invoice_line_item.price_subtotal / invoice_line_item.quantity / invoice_line_item.freight_currency_rate
    #                                         else:
    #                                             price_unit = invoice_line_item.price_subtotal / invoice_line_item.quantity
    #                                         if vendor_bill_line.type == 'in_invoice':
    #                                             total_cost = total_cost + price_unit
    #                                             total_qty = total_qty + invoice_line_item.quantity
    #                                         if vendor_bill_line.type == 'in_refund':
    #                                             # price_unit = invoice_line_item.price_subtotal / invoice_line_item.quantity
    #                                             total_cost = total_cost - price_unit
    #                                             total_qty = total_qty + invoice_line_item.quantity
    #                                         cost_profit_line.write({
    #                                             'cost_price': total_cost,
    #                                             'cost_qty': total_qty,  # why add 1
    #                                             # 'vendor_bill_ids': [(4, self.invoice_id.id)],
    #                                         })
    #                     else:
    #                         if self.freight_currency_rate != 1:
    #                             price_unit = self.price_subtotal / self.quantity / self.freight_currency_rate
    #                         else:
    #                             price_unit = self.price_subtotal / self.quantity
    #                         total_cost = total_cost + price_unit
    #                         total_qty += self.quantity
    #                         cost_profit_line.write({
    #                                 'cost_price': total_cost,
    #                                 'cost_qty': total_qty,  # why add 1
    #                                  'vendor_bill_ids': [(4, self.invoice_id.id)],
    #                         })
    #         # if check_booking:
    #         #    booking.action_calculate_cost()
    #         if not check_booking:
    #             raise exceptions.ValidationError('Product Not Found')

    @api.multi   #if remove the line items
    def unlink(self):
        for line in self:
            #print('>>>>>>>>>>>>>>>   Invoice Line Unlink')
            if line.booking_line_id:
                cost_line = self.env['freight.cost_profit'].browse(line.booking_line_id.id)
                #print('>>>>>>>>>>>>>>>   cost_line :', self.invoice_type)
                if self.invoice_type == 'in_invoice':   #vendor bill
                    vendor_bill_ids_list = []
                    if cost_line.vendor_bill_ids:
                        total_qty = 0
                        #qty_to_deduct = line.quantity
                        #cost_to_deduct = line.price_unit
                        #total_cost = cost_line.cost_total

                        #total_qty = cost_line.cost_qty
                        #print('>>>>>>>>>>>>>>>   qty_to_deduct :', qty_to_deduct)
                        #print('>>>>>>>>>>>>>>>   total_qty :', total_qty)
                        for vendor_bill in cost_line.vendor_bill_ids:
                            if vendor_bill.id != line.invoice_id.id:
                                vendor_bill_ids_list.append(vendor_bill.id)
                                account_invoice_line = self.env['account.invoice.line'].search([('invoice_id', '=',
                                                                                                 vendor_bill.id)])
                                for invoice_line_item in account_invoice_line:
                                    # print('>>>>>>>>>>  onchange_price_subtotal invoice_line_item.freight_booking=',
                                    #     invoice_line_item.freight_booking)
                                    if (invoice_line_item.product_id == cost_line.product_id) and \
                                            (invoice_line_item.freight_booking.id == cost_line.booking_id.id):
                                        total_qty = total_qty + invoice_line_item.quantity
                                        # print('>>>> onchange_price_subtotal price total_qty=', total_qty)
                        # TS - fix bug where after delete item, not working TODO
                        #total_qty = total_qty - qty_to_deduct
                        #print('>>>>>>>>>>>>>>>   total_qty 2:', total_qty)
                        if len(vendor_bill_ids_list) > 0:  #more than 1 vendor bills
                            cost_line.write({    #assuming cost_price will always be same for all vendor bills for same item
                                #'cost_price': round(price_unit, 2) or 0,
                                'cost_qty': total_qty or False,
                                #'cost_currency_rate': invoice_line.freight_currency_rate,
                                #'cost_currency': invoice_line.freight_currency.id,
                                'invoiced': True,
                                #'vendor_id': self.invoice_id.partner_id.id,
                                'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })
                        else:  #no more vendor bill
                        # TS - fix bug where after delete item, not working TODO
                            cost_line.write({
                                'cost_price': 0,
                                'cost_qty': 1 or False,
                                'cost_currency_rate': 1.000000,
                                # 'cost_currency': invoice_line.freight_currency.id,
                                'invoiced': False,
                                'paid': False,
                                'vendor_id': False,
                                'vendor_bill_ids': [(5, 0, 0)],    #delete all the items
                                #'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })
                    #reset from the current line
                    # TS - fix bug where after delete item, not working TODO
                    #line.booking_line_id.unlink()
                    line.booking_line_id.write({
                        'vendor_id_ids': [(3, line.invoice_id.partner_id.id)],
                        'vendor_bill_ids': [(3, line.invoice_id.id)],
                        'invoiced': False,
                        'added_to_invoice': False,
                    })
                    #print(cost_profit)
                elif self.invoice_type == 'out_invoice':
                    if self.invoice_id.freight_booking:
                        booking = self.env['freight.booking'].browse(self.invoice_id.freight_booking.id)
                        for cost_profit_line in booking.cost_profit_ids:
                            if cost_profit_line.product_id == line.product_id:
                                cost_profit_line.write({
                                    'list_price': 0,
                                    'profit_qty': 1 or False,
                                    'added_to_invoice': False,
                                })

                """
                if booking_line.invoice_type == 'in_refund':
                    cost_profit.write({
                        'vendor_bill_ids': [(3, cost_profit.invoice_id.id)],
                    })
                """

                #booking.action_calculate_cost_line()

            # if cost_profit.bl_line_id:
            #     bl_line = self.env['freight.bol.cost.profit'].browse(cost_profit.bl_line_id.id)
            #     bl_line.write({
            #         'added_to_invoice': False,
            #         'vendor_id': False,
            #         'vendor_bill_id': False,
            #         'invoiced': False,
            #         'cost_amount': 0,
            #         'cost_price': 0,
            #         'cost_qty': 0,
            #     })
        return super(AccountInvoiceLine, self).unlink()


    # @api.onchange('quantity', 'price_unit')
    # def _onchange_price(self):
    #     for cost_profit in self:
    #         if cost_profit.booking_line_id and not (
    #                 cost_profit.invoice_type == 'in_refund' or cost_profit.invoice_type == 'out_refund'):
    #             booking_line = self.env['freight.cost_profit'].browse(cost_profit.booking_line_id.id)
    #             if cost_profit.invoice_id.type == 'out_invoice':
    #                 list_price = cost_profit.price_unit / booking_line.profit_currency_rate
    #                 booking_line.write({
    #                     'list_price': list_price or 0,
    #                     'profit_qty': cost_profit.quantity or False,
    #                 })
    #             if cost_profit.invoice_id.type == 'in_invoice':
    #                 list_price = cost_profit.price_unit / booking_line.profit_currency_rate
    #                 #print(list_price)
    #                 #print(cost_profit.quantity)
    #                 booking_line.write({
    #                     'cost_price': list_price or 0,
    #                     'cost_qty': cost_profit.quantity or False,
    #                 })
    #
    #             booking_line.booking_id.action_calculate_cost()
    #
    #         if cost_profit.bl_line_id and not (
    #                 cost_profit.invoice_type == 'in_refund' or cost_profit.invoice_type == 'out_refund'):
    #             bl_line = self.env['freight.bol.cost.profit'].browse(cost_profit.bl_line_id.id)
    #             if cost_profit.invoice_id.type == 'out_invoice':
    #                 list_price = cost_profit.price_unit / bl_line.profit_currency_rate
    #                 bl_line.write({
    #                     'list_price': list_price or 0,
    #                     'profit_qty': cost_profit.quantity or False,
    #                 })
    #             if cost_profit.invoice_id.type == 'in_invoice':
    #                 list_price = cost_profit.price_unit / bl_line.profit_currency_rate
    #                 bl_line.write({
    #                     'cost_price': list_price or 0,
    #                     'cost_qty': cost_profit.quantity or False,
    #                 })
    #             bl_line.booking_id.action_calculate_cost()

    # @api.model
    # def create(self, vals):
    #     if vals.get('invoice_id'):
    #         invoice = self.env['account.invoice'].browse(vals.get('invoice_id'))
    #         product_id = vals.get('product_id')
    #         origin = vals.get('origin')
    #         if invoice.origin and invoice.type == 'out_invoice':
    #             booking = self.env['freight.booking'].search([('booking_no', '=', invoice.origin)])
    #             bl = self.env['freight.bol'].search([('bol_no', '=', invoice.origin)])
    #             if booking and not origin:
    #                 booking_line_obj = self.env['freight.cost_profit']
    #                 booking_line = booking_line_obj.create({
    #                     'product_id': product_id,
    #                     'product_name': vals.get('name'),
    #                     'profit_qty': vals.get('quantity'),
    #                     'list_price': vals.get('price_unit'),
    #                     'added_to_invoice': True,
    #                     'booking_id': booking.id or False,
    #                 })
    #                 vals['booking_line_id'] = booking_line.id
    #                 vals['account_analytic_id'] = booking.analytic_account_id.id
    #                 #booking.action_calculate_cost()
    #             if bl and not origin:
    #                 bl_line_obj = self.env['freight.bol.cost.profit']
    #                 bl_line = bl_line_obj.create({
    #                     'product_id': product_id,
    #                     'product_name': vals.get('name'),
    #                     'profit_qty': vals.get('quantity'),
    #                     'list_price': vals.get('price_unit'),
    #                     'added_to_invoice': True,
    #                     'bol_id': bl.id or False,
    #                 })
    #                 vals['bl_line_id'] = bl_line.id
    #                 vals['account_analytic_id'] = bl.analytic_account_id.id
    #     return super(AccountInvoiceLine, self).create(vals)
