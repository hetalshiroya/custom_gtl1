from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

class AccountInvoiceToReconcileWriteoff(models.TransientModel):
    """
    It opens the write off wizard form, in that user can define the journal, account, analytic account for reconcile
    """
    _name = 'account.invoice.to.reconcile.writeoff'
    _description = 'Account Invoice to reconcile (writeoff)'

    journal_id = fields.Many2one('account.journal', string='Write-Off Journal', required=True)
    writeoff_acc_id = fields.Many2one('account.account', string='Write-Off account', required=True, domain=[('deprecated', '=', False)])
    date_p = fields.Date(string='Date', default=fields.Date.context_today)
    residual = fields.Float(string='Write-Off amount', readonly=True, digits=0)
    comment = fields.Char(required=True, default='Write-off')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceToReconcileWriteoff, self).default_get(fields)
        data = self.trans_rec_get()
        if 'residual' in fields:
            res.update({'residual': data['residual']})
        return res
    
    @api.multi
    def trans_rec_get(self):
        context = self._context or {}
        amount_total = 0
        invoices = self.env['account.invoice'].browse(context.get('active_ids', []))
        for inv in invoices:
            amount_total += inv.residual
        precision = self.env.user.company_id.currency_id.decimal_places
        amount_total = float_round(amount_total, precision_digits=precision)
        return {'trans_nbr': len(invoices), 'residual': amount_total}

    @api.multi
    def trans_rec_reconcile(self):
        context = dict(self._context or {})
        context['date_p'] = self.date_p
        context['comment'] = self.comment
        if self.analytic_id:
            context['analytic_id'] = self.analytic_id.id
            
        invoice_lines = self.env['account.invoice'].browse(self._context.get('active_ids', []))
        #invoices = self.env[active_model].browse(active_ids)
        if any(invoice.state != 'open' for invoice in invoice_lines):
            raise UserError(_("You can only reconcile writeoff for open invoices"))
        if len(invoice_lines.mapped('account_id').ids) > 1:
            raise UserError(_('You can only reconcile writeoff invoice which have same account.'))
        invoice_lines.mapped('account_id').ids
        #print "====invoice_lines.mapped('move_id')===",invoice_lines.mapped('move_id')
        move_lines = invoice_lines.mapped('move_id').mapped('line_ids').filtered(lambda x: x.account_id.id in invoice_lines.mapped('account_id').ids)
        #move_lines = self.env['account.move.line'].browse(self._context.get('active_ids', []))
        #Don't consider entrires that are already reconciled
        move_lines_filtered = move_lines.filtered(lambda aml: not aml.reconciled)
        #Because we are making a full reconcilition in batch, we need to consider use cases as defined in the test test_manual_reconcile_wizard_opw678153
        #So we force the reconciliation in company currency only at first,
        context['skip_full_reconcile_check'] = 'amount_currency_excluded'
        writeoff = move_lines_filtered.with_context(context).reconcile(self.writeoff_acc_id, self.journal_id)
        #then in second pass, consider the amounts in secondary currency (only if some lines are still not fully reconciled)
        if not isinstance(writeoff, bool):
            move_lines += writeoff
        move_lines.check_full_reconcile()
        return {'type': 'ir.actions.act_window_close'}


