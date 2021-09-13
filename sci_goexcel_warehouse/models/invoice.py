from odoo import models, fields, api


class TallySheetInvoice(models.Model):

    _inherit = 'account.invoice'

    tally_sheet = fields.Many2one('warehouse.tally.sheet', string='Job Sheet', readonly=True)

    # for invoice only, invoice amount changes will update back to the job's cost & profit
    @api.onchange('amount_total')
    def onchange_amount_total(self):
        if self.tally_sheet:
            if self.type == 'out_invoice':
                #print("out_invoice")
                for line in self.invoice_line_ids:
                    tallysheet_cost_profit_lines = self.env['warehouse.cost.profit'].search([
                        ('inv_line_id', '=', line.id),
                    ])
                    if tallysheet_cost_profit_lines:
                        #print('freight_cost_profit_lines len:' + str(len(freight_cost_profit_lines)))
                        for cost_line in tallysheet_cost_profit_lines:
                            if line.price_subtotal != cost_line.sale_total:
                                #print('change sale total')
                                #print('line.price_subtotal=' + str(line.price_subtotal))
                                #print('sale_total=' + str(cost_line.sale_total))
                                #cost_line.sale_total = line.price_subtotal
                                #cost_line.profit_qty = line.quantity
                                value = {
                                    'sale_total': line.price_subtotal,
                                    'list_price': line.price_unit,
                                    'profit_qty': line.quantity,
                                }
                                #update to the existing line
                                # freight_cost_profit_lines.operation_id.write({
                                #     'cost_profit_ids': [
                                #         (1, cost_line.id, value),
                                #     ]
                                # })
                                if self.tally_sheet:
                                    self.tally_sheet.write({
                                        'cost_profit_ids': [
                                            (1, cost_line.id, value),
                                        ]
                                    })

    # update the invoice/vendor bill state Paid to tally sheet job status
    @api.multi
    def write(self, vals):
        res = super(TallySheetInvoice, self).write(vals)
        state = vals.get("state")
        #print('invoice state=' + str(state))
        #print('invoice residual=' + str(vals.get('residual')))
        if state == 'paid':
            if self.tally_sheet:
                if self.type == 'out_invoice':
                    tallysheets = self.env['warehouse.tally.sheet'].search([
                        ('id', '=', self.tally_sheet.id),
                    ])
                    #print('invoice len=' + str(len(bookings)))
                    #if tallysheets:
                    #    tallysheets[0].shipment_booking_status = '11'
                    invoice_cost_profit_ids = self.env['warehouse.cost.profit'].search([('invoice_id', '=', self.id),])
                    print(invoice_cost_profit_ids)
                    for cost_profit_id in invoice_cost_profit_ids:
                        cost_profit_id.invoice_paid = True
                        tallysheets[0].invoice_paid_status = '02'
                    check_all_paid = True
                    for check_line in tallysheets[0].cost_profit_ids:
                        if not check_line.invoice_paid:
                            check_all_paid = False
                    if check_all_paid:
                        tallysheets[0].invoice_paid_status = '03'

                elif self.type == 'in_invoice':
                    tallysheets = self.env['warehouse.tally.sheet'].search([
                        ('id', '=', self.tally_sheet.id),
                    ])
                    #print('booking len=' + str(len(tallysheets)))
                    if tallysheets:
                        vendor_cost_profit_ids = tallysheets[0].cost_profit_ids.filtered(lambda r: r.vendor_id.id == self.partner_id.id)
                        #print('vendor_cost_profit_ids len=' + str(len(vendor_cost_profit_ids)))
                        for cost_profit_id in vendor_cost_profit_ids:
                            cost_profit_id.paid = True
            else:
                #assign cost
                if self.type == 'in_invoice':
                    for line in self.invoice_line_ids:
                        if line.tally_sheet:
                            tallysheet_cost_profit_lines = self.env['warehouse.cost.profit'].search([
                                ('bill_line_id', '=', line.id),
                            ])
                            if tallysheet_cost_profit_lines:
                                for cost_line in tallysheet_cost_profit_lines:
                                   cost_line.paid = True

        return res



class TallySheetInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    #booking_job_cost = fields.Many2one('freight.cost_profit', string='Job Cost')
    tally_sheet= fields.Many2one('warehouse.tally.sheet', string='Job Sheet')
