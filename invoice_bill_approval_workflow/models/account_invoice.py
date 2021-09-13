# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _description = "Invoice Validate View"
    #_inherit = ['account.invoice', 'mail.thread', 'mail.activity.mixin']

    approve_by = fields.Many2one(
        'res.users', string='Approved By', track_visibility='always', copy=False)
    approve_date_time = fields.Datetime(string='Approved Date', track_visibility='always', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'To Approve'),
        ('open', 'Open'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='always', copy=False)

    @api.multi
    def action_invoice_open_ip(self):
        ammount = self.filtered(lambda inv: inv.state != 'open')
        if self.company_id.invoice_bill_approval or self.company_id.customer_vendor_credit_approval:
            ctx = {}
            list_of_user = False
            action = self.env.ref('account.action_invoice_tree1').id
            if self.type == 'out_invoice':
                ammount = self.company_id.invoice_ammount
                list_of_user = self.company_id.invoice_user_ids
                ctx['type'] = 'Invoice'
            elif self.type == 'in_invoice':
                ammount = self.company_id.bill_ammount
                list_of_user = self.company_id.bill_user_ids
                ctx['type'] = 'Bill'
                action = self.env.ref('account.action_vendor_bill_template').id
            elif self.type == 'out_refund':
                ammount = self.company_id.customer_credit_note_ammount_ammount
                list_of_user = self.company_id.invoice_cn_user_ids
                ctx['type'] = 'Customer Credit Note'
                action = self.env.ref('account.action_invoice_out_refund').id
            elif self.type == 'in_refund':
                ammount = self.company_id.vendor_credit_note_ammount
                list_of_user = self.company_id.bill_cn_user_ids
                ctx['type'] = 'Vendor Credit Note'
                action = self.env.ref('account.action_invoice_in_refund').id

            if self.amount_total < float(ammount):
                self.action_invoice_open()
            else:
                # change email list by shivam
                # email_list = [user.email for user in self.env['res.users'].sudo().search([('company_ids', 'in', self.company_id.ids)]) if user.has_group('account.group_account_manager')]
                email_list = [user.email for user in list_of_user]
                if email_list:
                    ctx['partner_manager_email'] = ','.join([email for email in email_list if email])
                    ctx['email_from'] = self.env.user.email
                    ctx['partner_name'] = self.env.user.name
                    ctx['customer_name'] = self.partner_id.name
                    ctx['amount_total'] = self.amount_total
                    ctx['lang'] = self.env.user.lang
                    template = self.env.ref('invoice_bill_approval_workflow.invoice_bill_validate_email_template_ip')
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    ctx['action_url'] = "{}/web?db={}#id={}&action={}&view_type=form&model=account.invoice".format(
                        base_url, self.env.cr.dbname, self.id, action)
                    template.with_context(ctx).sudo().send_mail(self.id, force_send=True, raise_exception=False)
                self.write({'state': 'approve'})
        else:
            self.action_invoice_open()

    @api.multi
    def action_invoice_approve(self):
        print('Approved - ' + str(self.env.user.id))
        self.write({'state': 'draft'})
        self.approve_by = self.env.user.id
        self.approve_date_time = datetime.now()
        self.action_invoice_open()

    @api.multi
    def action_invoice_reject(self):
        self.write({'state': 'draft'})
        # self.action_invoice_draft()

    @api.multi
    def create_action(self):
        global model
        for report in self:
            model = self.en.env['ir.model']._get(report.model)
        report.write({'binding_model_id': model.id, 'binding_type': 'report'})
        return True

    @api.multi
    def unlink_action(self):
        self.check_access_rights('write', raise_exception=True)
        self.filtered('binding_model_id').write({'binding_model_id': False})
        return True


class InvoiceReport(models.Model):
    _name = 'report.account.report_invoice'
    _description = 'Invoice Report'

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.invoice.report'].browse(docids)
        for doc in docs:
            if doc.state != 'open':
                raise exceptions.ValidationError('Please approve the order to print the report.')
            return {
                'doc_ids': docs.ids,
                'doc_model': 'account.invoice.report',
                'docs': docs,
                'proforma': True
            }
