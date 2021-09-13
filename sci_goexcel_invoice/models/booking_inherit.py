from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    @api.multi
    def action_create_vendor_bill(self):
        # only lines with vendor
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        # print('vendor_po=' + str(len(vendor_po)))
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        # print('po_lines=' + str(len(po_lines)))
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'partner_id': self.customer_name.id,
                'name': '%s' % self.booking_no,
                # 'partner_id': self.customer_name.id,
                'company_id': self.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            # print(line.vendor_bill_id)
            # print('line.vendor_id=' + line.vendor_id.name)
            if line.vendor_id != vendor_id:
                # print('not same partner')
                vb = self.env['account.invoice']
                # vb_line_obj = self.env['account.invoice.line']
                # if line.vendor_id:
                vendor_count = True
                vendor_id = line.vendor_id
                # print('vendor_id=' + vendor_id.name)
                # combine multiple cost lines from same vendor
                value = []
                vendor_bill_created = []
                filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                for vb_line in filtered_vb_lines:
                    # print('combine lines')
                    if not vb_line.invoiced:
                        account_id = False
                        # price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                        price_after_converted = round(vb_line.cost_price * vb_line.cost_currency_rate, 6)
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        # print(vb_line)
                        value.append([0, 0, {
                            # 'invoice_id': vendor_bill.id or False,
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'quantity': vb_line.cost_qty or 0.0,
                            'uom_id': vb_line.uom_id.id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                            'freight_booking': self.id,
                            'booking_line_id': vb_line.id,
                            'freight_currency': vb_line.cost_currency.id or False,
                            'freight_foreign_price': vb_line.cost_price or 0.0,
                            'freight_currency_rate': round(vb_line.cost_currency_rate, 6) or 1.000000,
                        }])
                        vendor_bill_created.append(vb_line)
                        vb_line.invoiced = True

                vendor_bill_list = []
                if value:
                    vendor_bill_id = vb.create({
                        'type': 'in_invoice',
                        'invoice_line_ids': value,
                        #  'default_purchase_id': self.booking_no,
                        'default_currency_id': self.env.user.company_id.currency_id.id,
                        'company_id': self.company_id.id,
                        'date_invoice': fields.Date.context_today(self),
                        'origin': self.booking_no,
                        'partner_id': vendor_id.id,
                        'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                        'freight_booking': self.id,
                    })
                    vendor_bill_list.append(vendor_bill_id.id)
                for vb_line in filtered_vb_lines:
                    if vb_line.invoiced:
                        vendor_bill_ids_list = []
                        if vendor_bill_list:
                            vendor_bill_ids_list.append(vendor_bill_list[0])
                            vb_line.write({
                                # 'vendor_id_ids': [(6, 0, vendor_ids_list)],
                                'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })
                # for new_vendor_bill in vendor_bill_created:
                #     new_vendor_bill.vendor_bill_id = vendor_bill_id.id
                #     new_vendor_bill.vendor_bill_ids = [(6, 0, vendor_bill_list)]
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        for operation in self:
            # Get from the vendor bill list
            vendor_bill_list = []
            # vendor_bill_list_temp = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)
                        # vendor_bill_list_temp.append(vendor_bill_line.id)
            #print('vendor_bill_list: ', len(vendor_bill_list))
            # remove the duplicates in the vendor bill list
            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)
            #print('unique_vendor_bill_list: ', len(unique_vendor_bill_list))
            # Get the vendor list (Create the vendor from the job)
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            #print('vendor bills:', len(invoices))
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)
            unique_list = []
            # for x in invoices:
            #     invoice_name_list.append(x.vendor_bill_id.id)
            # unique_list = []
            for y in unique_vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)
            if len(unique_list) > 0:
                self.update({
                    'vendor_bill_count': len(unique_list),
                })
            # else:
            #     # self.update({
            #     #     'vendor_bill_count': len(unique_list),
            #     # })
            #     #TS - show vendor bill count for old vendor bills
            #     invoices = self.env['account.invoice'].search([
            #         ('freight_booking', '=', operation.id),
            #         ('type', '=', 'in_invoice'),
            #         ('state', '!=', 'cancel'),
            #     ])
            #     if len(invoices) > 0:
            #         self.update({
            #             'vendor_bill_count': len(invoices),
            #         })

    @api.multi
    def operation_bill(self):
        for operation in self:
            """
            invoices = self.env['account.invoice'].search([
                ('origin', '=', self.booking_no),
                ('type', '=', 'in_invoice'),
            ])
            """
            vendor_bill_list = []
            for cost_profit_line in operation.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', operation.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            invoice_name_list = []
            for x in invoices:
                invoice_name_list.append(x.id)

            unique_list = []
            for y in vendor_bill_list:
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                else:
                    unique_list.append(y)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)

        if len(unique_list) > 1:
            context = dict(self.env.context or {})
            context.update(create=False)
            views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                     (self.env.ref('account.invoice_supplier_form').id, 'form')]
            return {
                'name': 'Vendor bills',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.invoice',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'context': context,
                'domain': [('id', 'in', unique_list)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(unique_list) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


    # def _get_bill_count(self):
    #     for operation in self:
    #         vendor_bill_list = []
    #         for cost_profit_line in operation.cost_profit_ids:
    #             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                 if vendor_bill_line.type == 'in_invoice':
    #                     vendor_bill_list.append(vendor_bill_line.id)
    #
    #         unique_list = []
    #         for y in vendor_bill_list:
    #             if y not in unique_list:
    #                 unique_list.append(y)
    #         self.update({
    #             'vendor_bill_count': len(unique_list),
    #         })
    #
    #
    # @api.multi
    # def operation_bill(self):
    #     for operation in self:
    #         """
    #         invoices = self.env['account.invoice'].search([
    #             ('origin', '=', self.booking_no),
    #             ('type', '=', 'in_invoice'),
    #         ])
    #         """
    #         vendor_bill_list = []
    #         for cost_profit_line in operation.cost_profit_ids:
    #             for vendor_bill_line in cost_profit_line.vendor_bill_ids:
    #                 if vendor_bill_line.type == 'in_invoice':
    #                     vendor_bill_list.append(vendor_bill_line.id)
    #
    #         invoices = self.env['account.invoice'].search([
    #             ('freight_booking', '=', operation.id),
    #             ('type', '=', 'in_invoice'),
    #             ('state', '!=', 'cancel'),
    #         ])
    #         invoice_name_list = []
    #         for x in invoices:
    #             invoice_name_list.append(x.id)
    #
    #         unique_list = []
    #         for y in vendor_bill_list:
    #             if invoice_name_list and len(invoice_name_list) > 0:
    #                 if y not in invoice_name_list:
    #                     unique_list.append(y)
    #             else:
    #                 unique_list.append(y)
    #         for z in invoice_name_list:
    #             # if z not in vendor_bill_list:
    #             unique_list.append(z)
    #
    #     if len(unique_list) > 1:
    #         views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
    #                  (self.env.ref('account.invoice_supplier_form').id, 'form')]
    #         return {
    #             'name': 'Vendor bills',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
    #             'view_id': False,
    #             'res_model': 'account.invoice',
    #             'views': views,
    #             # 'context': "{'type':'in_invoice'}",
    #             'domain': [('id', 'in', unique_list)],
    #             'type': 'ir.actions.act_window',
    #             # 'target': 'new',
    #         }
    #     elif len(unique_list) == 1:
    #         # print('in vendor bill length =1')
    #         return {
    #             # 'name': self.booking_no,
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'account.invoice',
    #             'res_id': unique_list[0] or False,  # readonly mode
    #             #  'domain': [('id', 'in', purchase_order.ids)],
    #             'type': 'ir.actions.act_window',
    #             'target': 'popup',  # readonly mode
    #         }
    #
    # @api.multi
    # def action_create_vendor_bill(self):
    #     vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
    #     po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
    #     vendor_count = False
    #     vendor_id = False
    #     if not self.analytic_account_id:
    #         values = {
    #             'name': '%s' % self.booking_no,
    #             # 'partner_id': self.customer_name.id,
    #             'company_id': self.company_id.id,
    #         }
    #         analytic_account = self.env['account.analytic.account'].sudo().create(values)
    #         self.write({'analytic_account_id': analytic_account.id})
    #     for line in po_lines:
    #         #print(line.vendor_bill_id)
    #         # print('line.vendor_id=' + line.vendor_id.name)
    #         if line.vendor_id != vendor_id:
    #             #print('not same partner')
    #             vb = self.env['account.invoice']
    #             vendor_count = True
    #             vendor_id = line.vendor_id
    #             value = []
    #             vendor_bill_created = []
    #             filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
    #             for vb_line in filtered_vb_lines:
    #                 if not vb_line.invoiced:
    #                     account_id = False
    #                     price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
    #                     if vb_line.product_id.property_account_expense_id:
    #                         account_id = vb_line.product_id.property_account_expense_id
    #                     elif vb_line.product_id.categ_id.property_account_expense_categ_id:
    #                         account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
    #                     value.append([0, 0, {
    #                         # 'invoice_id': vendor_bill.id or False,
    #                         'account_id': account_id.id or False,
    #                         'name': vb_line.product_id.name or '',
    #                         'product_id': vb_line.product_id.id or False,
    #                         'quantity': vb_line.cost_qty or 0.0,
    #                         'uom_id': vb_line.uom_id.id or False,
    #                         'price_unit': price_after_converted or 0.0,
    #                         'account_analytic_id': self.analytic_account_id.id,
    #                         'freight_booking': self.id,
    #                         'booking_line_id': vb_line.id,
    #                     }])
    #                     vendor_bill_created.append(vb_line)
    #                     vb_line.invoiced = True
    #             vendor_bill_list = []
    #             if value:
    #                 vendor_bill_id = vb.create({
    #                     'type': 'in_invoice',
    #                     'invoice_line_ids': value,
    #                     'default_currency_id': self.env.user.company_id.currency_id.id,
    #                     'company_id': self.company_id.id,
    #                     'date_invoice': fields.Date.context_today(self),
    #                     'partner_id': vendor_id.id,
    #                     'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
    #                     'freight_booking': self.id,
    #                 })
    #                 vendor_bill_list.append(vendor_bill_id.id)
    #             #print(vendor_bill_list)
    #             for new_vendor_bill in vendor_bill_created:
    #                 new_vendor_bill.vendor_bill_id = vendor_bill_id.id
    #                 new_vendor_bill.vendor_bill_ids = [(6, 0, vendor_bill_list)]
    #     if vendor_count is False:
    #         raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')


class CostProfit(models.Model):
    _inherit = "freight.cost_profit"

    vendor_id_ids = fields.Many2many('res.partner', string="Vendor List", copy=False)
    vendor_bill_ids = fields.Many2many('account.invoice', string="Vendor Bill List", copy=False)

#
# class BookingInvoiceLines(models.Model):
#     _name = "booking.invoice.line"
#
#     #invoice_id = fields.Many2one('account.invoice', string="Invoice")
#     invoice_no = fields.Char(string="Invoice No")
#     reference = fields.Char(string="Vendor Invoice/Payment Ref.")
#     invoice_amount = fields.Float(string="Amount", store=True)
#     #type = fields.Char(string='type', help="invoice, vendor bill, customer CN and vendor CN, vendor debit note")
#     booking_id = fields.Many2one('freight.booking', string='Booking Reference', required=True, ondelete='cascade',
#                     index=True, copy=False)