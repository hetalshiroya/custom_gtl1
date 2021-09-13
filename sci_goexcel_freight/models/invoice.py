from odoo import models, fields, api


class FreightInvoice(models.Model):
    _inherit = 'account.invoice'

    freight_booking = fields.Many2one('freight.booking', string='Freight Booking')
    # update_paid = fields.Boolean(string='Update Booking Job to Paid', compute='_update_booking_paid')

    # for invoice only, invoice amount changes will update back to the job's cost & profit
    # @api.onchange('amount_total')
    # def onchange_amount_total(self):
    #     if self.freight_booking:
    #         if self.type == 'out_invoice':
    #             # print("out_invoice")
    #             for line in self.invoice_line_ids:
    #                 freight_cost_profit_lines = self.env['freight.cost_profit'].search([
    #                     ('inv_line_id', '=', line.id),
    #                 ])
    #                 if freight_cost_profit_lines:
    #                     # print('freight_cost_profit_lines len:' + str(len(freight_cost_profit_lines)))
    #                     for cost_line in freight_cost_profit_lines:
    #                         if line.price_subtotal != cost_line.sale_total:
    #                             # print('change sale total')
    #                             # print('line.price_subtotal=' + str(line.price_subtotal))
    #                             # print('sale_total=' + str(cost_line.sale_total))
    #                             # cost_line.sale_total = line.price_subtotal
    #                             # cost_line.profit_qty = line.quantity
    #                             value = {
    #                                 'sale_total': line.price_subtotal,
    #                                 'list_price': line.price_unit,
    #                                 'profit_qty': line.quantity,
    #                             }
    #                             # update to the existing line
    #                             # freight_cost_profit_lines.operation_id.write({
    #                             #     'cost_profit_ids': [
    #                             #         (1, cost_line.id, value),
    #                             #     ]
    #                             # })
    #                             if self.freight_booking:
    #                                 self.freight_booking.write({
    #                                     'cost_profit_ids': [
    #                                         (1, cost_line.id, value),
    #                                     ]
    #                                 })

    # @api.onchange('state')
    # def _onchange_state(self):
    #     #update the invoice status Paid to freight booking job status
    #     print('invoice depends state')
    #     if self.state == 'paid':
    #         if self.freight_booking:
    #             if self.type == 'out_invoice':
    #                 bookings = self.env['freight.booking'].search([
    #                     ('id', '=', self.freight_booking.id),
    #                 ])
    #                 print('invoice onchange_state invoice len=' + str(len(bookings)))
    #                 bookings[0].shipment_booking_status = '11'

    # @api.depends('state','residual')
    # def _update_booking_paid(self):
    #     #update the invoice status Paid to freight booking job status
    #     print('invoice depends state')
    #     for invoice in self:
    #         print('invoice state=' + invoice.state)
    #         print('invoice residual=' + str(invoice.residual))
    #         if invoice.state == 'paid':
    #             if invoice.freight_booking:
    #                 if invoice.type == 'out_invoice':
    #                     bookings = self.env['freight.booking'].search([
    #                         ('id', '=', invoice.freight_booking.id),
    #                     ])
    #                     invoice.update_paid = True
    #                     print('invoice onchange_state invoice len=' + str(len(bookings)))
    #                     if bookings:
    #                         bookings[0].shipment_booking_status = '11'

    # update the invoice/vendor bill state Paid to freight booking job status
    @api.multi
    def write(self, vals):
        res = super(FreightInvoice, self).write(vals)
        state = vals.get("state")
        if state == 'paid':
            if self.freight_booking:
                if self.type == 'out_invoice':
                    bookings = self.env['freight.booking'].search([
                        ('id', '=', self.freight_booking.id),
                    ])
                    # print('invoice len=' + str(len(bookings)))
                    if bookings:
                        bookings[0].shipment_booking_status = '11'
                    invoice_cost_profit_ids = self.env['freight.cost_profit'].search([('invoice_id', '=', self.id), ])
                    print(invoice_cost_profit_ids)
                    for cost_profit_id in invoice_cost_profit_ids:
                        cost_profit_id.invoice_paid = True
                        bookings[0].invoice_paid_status = '02'
                    check_all_paid = True
                    for check_line in bookings[0].cost_profit_ids:
                        if not check_line.invoice_paid:
                            check_all_paid = False
                    if check_all_paid:
                        bookings[0].invoice_paid_status = '03'

                elif self.type == 'in_invoice':
                    bookings = self.env['freight.booking'].search([
                        ('id', '=', self.freight_booking.id),
                    ])
                    print('booking len=' + str(len(bookings)))
                    if bookings:
                        vendor_cost_profit_ids = bookings[0].cost_profit_ids.filtered(
                            lambda r: r.vendor_id.id == self.partner_id.id)
                        print('vendor_cost_profit_ids len=' + str(len(vendor_cost_profit_ids)))
                        for cost_profit_id in vendor_cost_profit_ids:
                            cost_profit_id.paid = True
            else:
                # assign cost
                if self.type == 'in_invoice':
                    for line in self.invoice_line_ids:
                        if line.freight_booking:
                            freight_cost_profit_lines = self.env['freight.cost_profit'].search([
                                ('bill_line_id', '=', line.id),
                            ])
                            if freight_cost_profit_lines:
                                for cost_line in freight_cost_profit_lines:
                                    cost_line.paid = True

        return res
    # @api.multi
    # @api.depends('residual')
    # def check_invoice_status_residual(self):
    #     # update the invoice status Paid to freight booking job status
    #     print('invoice residual')
    #     if self.state == 'paid':
    #         if self.freight_booking:
    #             if self.type == 'out_invoice':
    #                 bookings = self.env['freight.booking'].search([
    #                     ('id', '=', self.freight_booking.id),
    #                 ])
    #                 print('invoice onchange_state invoice len=' + str(len(bookings)))
    #                 bookings[0].shipment_booking_status = '11'


class FreightInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    """
    booking_line_id = fields.Many2one('freight.cost_profit', copy=False)
    bl_line_id = fields.Many2one('freight.bol.cost.profit', copy=False)

    @api.onchange('quantity', 'price_unit')
    def _onchange_price(self):
        for cost_profit in self:
            if cost_profit.booking_line_id and not (cost_profit.invoice_type == 'in_refund' or cost_profit.invoice_type == 'out_refund'):
                booking_line = self.env['freight.cost_profit'].browse(cost_profit.booking_line_id.id)
                if cost_profit.invoice_id.type == 'out_invoice':
                    list_price = cost_profit.price_unit / booking_line.profit_currency_rate
                    booking_line.write({
                        'list_price': list_price or 0,
                        'profit_qty': cost_profit.quantity or False,
                    })
                if cost_profit.invoice_id.type == 'in_invoice':
                    list_price = cost_profit.price_unit / booking_line.profit_currency_rate
                    print(list_price)
                    print(cost_profit.quantity)
                    booking_line.write({
                        'cost_price': list_price or 0,
                        'cost_qty': cost_profit.quantity or False,
                    })

            if cost_profit.bl_line_id and not (cost_profit.invoice_type == 'in_refund' or cost_profit.invoice_type == 'out_refund'):
                bl_line = self.env['freight.bol.cost.profit'].browse(cost_profit.bl_line_id.id)
                if cost_profit.invoice_id.type == 'out_invoice':
                    list_price = cost_profit.price_unit / bl_line.profit_currency_rate
                    bl_line.write({
                        'list_price': list_price or 0,
                        'profit_qty': cost_profit.quantity or False,
                    })
                if cost_profit.invoice_id.type == 'in_invoice':
                    list_price = cost_profit.price_unit / bl_line.profit_currency_rate
                    bl_line.write({
                        'cost_price': list_price or 0,
                        'cost_qty': cost_profit.quantity or False,
                    })

    @api.multi
    def unlink(self):
        for cost_profit in self:
            print('Ready To Delete')
            if cost_profit.booking_line_id:
                booking_line = self.env['freight.cost_profit'].browse(cost_profit.booking_line_id.id)
                booking_line.write({
                    'added_to_invoice': False,
                })
            if cost_profit.bl_line_id:
                bl_line = self.env['freight.bol.cost.profit'].browse(cost_profit.bl_line_id.id)
                bl_line.write({
                    'added_to_invoice': False,
                })
        return super(FreightInvoiceLine, self).unlink()

    @api.model
    def create(self, vals):
        invoice = self.env['account.invoice'].browse(vals.get('invoice_id'))
        product_id = vals.get('product_id')
        origin = vals.get('origin')
        if invoice.origin and invoice.type == 'out_invoice':
            booking = self.env['freight.booking'].search([('booking_no', '=', invoice.origin)])
            bl = self.env['freight.bol'].search([('bol_no', '=', invoice.origin)])
            if booking and not origin:
                booking_line_obj = self.env['freight.cost_profit']
                booking_line = booking_line_obj.create({
                    'product_id': product_id,
                    'product_name': vals.get('name'),
                    'profit_qty': vals.get('quantity'),
                    'list_price': vals.get('price_unit'),
                    'added_to_invoice': True,
                    'booking_id': booking.id or False,
                })
                vals['booking_line_id'] = booking_line.id
                vals['account_analytic_id'] = booking.analytic_account_id.id
            if bl and not origin:
                bl_line_obj = self.env['freight.bol.cost.profit']
                bl_line = bl_line_obj.create({
                    'product_id': product_id,
                    'product_name': vals.get('name'),
                    'profit_qty': vals.get('quantity'),
                    'list_price': vals.get('price_unit'),
                    'added_to_invoice': True,
                    'bol_id': bl.id or False,
                })
                vals['bl_line_id'] = bl_line.id
                vals['account_analytic_id'] = bl.analytic_account_id.id
        return super(FreightInvoiceLine, self).create(vals)
    """

