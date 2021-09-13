from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountDebitnoteReport(models.TransientModel):
    """Debit Notes"""

    _name = 'account.debitnote.report'
    _description = "Debit Note Report"

    partner_ids = fields.Many2many(
        'res.partner',
        string='Partner',
    )
    date_from = fields.Date(
        string='Invoice Date From',
        default=fields.Date.context_today,
        required=True,
    )
    date_to = fields.Date(
        string='Invoice Date To',
        default=fields.Date.context_today,
        required=True,
    )
    filter_debit = fields.Selection(
        [('debit', 'Debit notes'),('credit', 'Credit notes'),('invoice', 'Invoice'), ('bill', 'Vendor Bill')],
        string='Type',
        default='invoice',
        required=True,
    )
    balance = fields.Boolean(string='With Amount Due', default=True)


    def get_report_values(self):
        # Find partners
        partner_ids = self.partner_ids
        if not partner_ids:
            partner_ids = self.env['res.partner'].search(['|',('customer','=',True),('supplier','=',True)])

        # Fetch partner related lines
        output = []
        output.append({
            'type': self.filter_debit,
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        for partner in partner_ids:
            if self.balance:
                domain = [('partner_id', '=', partner.id),
                          ('date_invoice', '>=', self.date_from),
                          ('date_invoice', '<=', self.date_to),
                          ('state', 'in', ['open'])]
            else:
                domain = [('partner_id','=',partner.id),
                          ('date_invoice','>=',self.date_from),
                          ('date_invoice','<=',self.date_to),
                          ('state','in',['open','paid'])]
            if self.filter_debit == 'debit':
                domain.append('|')
                domain.append(('debit_invoice_id.id','>',0))
                domain.append(('type','=','in_invoice'))
            if self.filter_debit == 'credit':
                domain.append('|')
                domain.append(('debit_invoice_id.id','>',0))
                domain.append(('type','=','out_invoice'))
            if self.filter_debit == 'invoice':
                # domain.append('|')
                # domain.append(('customer_debit_note', '=', False))
                domain.append(('type', '=', 'out_invoice'))
            if self.filter_debit == 'bill':
                # domain.append('|')
                #domain.append(('debit_invoice_id.id', '>', 0))
                domain.append(('type', '=', 'in_invoice'))
            for inv in self.env['account.invoice'].search(domain, order="date_invoice asc"):
                # fetch sub lines
                sub_lines = []
                for payment_val in inv._get_payments_vals():
                    dict = {
                        'date': payment_val.get('date'),
                        'doc_number': payment_val.get('name'),
                        'description': payment_val.get('ref'),
                        'doc_amount': float(payment_val.get('amount')),
                        'knockoff_amount': float(payment_val.get('amount')),
                    }
                    move_line_id = self.env['account.move.line'].browse(int(payment_val.get('payment_id')))
                    dict.update({'doc_amount': move_line_id.payment_id.amount})
                    sub_lines.append(dict)

                #if self.balance and not sum([a.get('doc_amount') for a in sub_lines]):
                #     continue

                partner_dict = {
                    'partner_id': inv.partner_id,
                    'partner_name': inv.partner_id.name,
                    'doc_date': inv.date_invoice,
                    'code': inv.reference,
                    'doc_number': inv.number,
                    'total_amount': inv.amount_total,
                    'amount': inv.residual,
                    'sub_lines':sub_lines
                }
                output.append(partner_dict)
        return self.env.ref(
            'account_debitnote.ins_debitnote_report_pdf').report_action(self,
                                                                        {'data':output, 'filter':self.filter_debit})
        return output


class DebitnoteReportPdf(models.AbstractModel):
    """ Abstract model for generating PDF report value and send to template common for P and L and Balance Sheet"""

    _name = 'report.account_debitnote.account_debitnote_report'
    _description = 'Debit Note Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ Provide report values to template """
        return data