# from odoo import api, fields, models,exceptions
# import logging
# from datetime import date
# _logger = logging.getLogger(__name__)
#
#
# class AccountInvoiceLine(models.Model):
#
#     _inherit = 'account.invoice.line'


    # @api.onchange('invoice_line_tax_ids')
    # def _onchange_invoice_line_tax_ids(self):
    #     print('onchange invoice_line_tax_ids')
    #     if self.invoice_line_tax_ids:
    #         if self.invoice_id.type == 'out_refund':
    #             print('CN')
    #             if not self.invoice_id.tax_line_ids:
    #                 account_invoice_tax = self.invoice_id.env['account.invoice.tax']
    #                 #ctx = dict(self.invoice_id._context)
    #                 #self.invoice_id._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False",
    #                 #                 (self.invoice_id.id,))
    #                 #if self.invoice_id._cr.rowcount:
    #                 #    self.invoice_id.invalidate_cache()
    #                 tax_grouped = self.invoice_id.get_taxes_values()
    #                 for tax in tax_grouped.values():
    #                     #print('tax=', tax)
    #                     #self.invoice_id.tax_line_ids = [(0, 0, tax)]
    #                     tax_lines = self.invoice_id.tax_line_ids.ids
    #                     tax_lines.append(tax.id)
    #                     self.invoice_id.tax_line_ids = [(0, 0, tax_lines)]

                        #account_invoice_tax.create(tax)

                    #self.invoice_id.write({'invoice_line_ids': []})
                    #account_invoice_tax = self.env['account.invoice.tax']
                    #tax_lines = self.tax_line_ids.filtered('manual')
                    #for tax in taxes_grouped.values():
                    #    self.tax_line_ids = account_invoice_tax.create(tax)
                        #tax_lines += tax_lines.new(tax)
                    #self.tax_line_ids = tax_lines


