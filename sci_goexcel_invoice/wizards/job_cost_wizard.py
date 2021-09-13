from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions


class FreightBookingJobCost(models.TransientModel):
    _name = 'job.cost.wizard'

    booking_job_no = fields.Char(string='Booking Job No', help='Enter Booking Job No to search for Job Cost')
    carrier_job_no = fields.Char(string='Carrier Job No', help='Enter Carrier Booking No to search for Job Cost')
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain="[('supplier','=',True)]")
    vendor_bill_id = fields.Many2one('account.invoice', string='Vendor Bill')
    customer_name = fields.Many2one('res.partner', string='Customer')
    job_cost_lines = fields.One2many('job.cost.wizard.line', 'job_cost_id')

    product_id = fields.Many2one('product.product', string='Product')


    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        rec.update({
            'vendor_id': self.env.context.get('partner_id'),
            'vendor_bill_id': self.env.context.get('vendor_bill_id'),
        })
        return rec

    @api.onchange('booking_job_no', 'carrier_job_no')
    def onchange_booking_job_no(self):
        job_cost_line = self.env['job.cost.wizard.line']
        line_list = []
        for job_cost in self:
            invoice = self.env['account.invoice'].search([('id', '=', self.env.context.get('vendor_bill_id'))], limit=1)
            if job_cost.booking_job_no or job_cost.carrier_job_no:
                if job_cost.booking_job_no:
                    bookings = self.env['freight.booking'].search([('booking_no', '=', job_cost.booking_job_no)], limit=1)

                if job_cost.carrier_job_no:
                    bookings = self.env['freight.booking'].search([('carrier_booking_no', '=', job_cost.carrier_job_no)], limit=1)
                for booking in bookings:

                    job_cost.customer_name = booking.customer_name.id
                    for booking_line in booking.cost_profit_ids:
                        matched = False
                        add = False
                        for invoice_line in invoice.invoice_line_ids:
                            if invoice_line.product_id == booking_line.product_id:
                                matched = True
                                add = True
                        if booking_line.invoiced:
                            add = False
                        vals = ({
                            'matched' : matched,
                            'add_to_vendor_bill': add,
                            'billed': booking_line.invoiced,
                            'booking_id': booking.id,
                            'booking_line_id': booking_line.id,
                            'product_id': booking_line.product_id.id,
                            'product_name': booking_line.product_name,
                            'list_price': booking_line.list_price,
                            'profit_amount': booking_line.profit_amount,
                            'sale_total': booking_line.sale_total,
                            'cost_qty': booking_line.cost_qty,
                            'cost_price': booking_line.cost_price,
                            'cost_amount': booking_line.cost_amount,
                            'cost_total': booking_line.cost_total,
                            'profit_total': booking_line.profit_total,
                            'cost_profit_line': booking_line,
                        })
                        new_job_cost = job_cost_line.create(vals)
                        line_list.append(new_job_cost.id)
            job_cost.job_cost_lines = line_list

    @api.multi
    def action_assign_job_cost(self):
        invoice = self.env['account.invoice'].search([('id', '=', self.env.context.get('vendor_bill_id'))], limit=1)

        for job_cost in self.job_cost_lines:
            if self.booking_job_no:
                booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_job_no)], limit=1)
            if self.carrier_job_no:
                booking = self.env['freight.booking'].search([('carrier_booking_no', '=', self.carrier_job_no)],limit=1)
            if not booking.analytic_account_id:
                values = {
                    'partner_id': booking.customer_name.id,
                    'name': '%s' % booking.booking_no,
                    'company_id': self.env.user.company_id.id,
                }
                analytic_account = self.env['account.analytic.account'].sudo().create(values)
                booking.write({'analytic_account_id': analytic_account.id,
                               })

            if job_cost.add_to_vendor_bill:
                check_same_product = 0
                for invoice_line1 in invoice.invoice_line_ids:
                    if invoice_line1.product_id == job_cost.product_id:
                        check_same_product = check_same_product + 1
                if check_same_product == 1:
                    for invoice_line in invoice.invoice_line_ids:
                        if invoice_line.product_id == job_cost.product_id:
                            invoice_line.freight_booking = job_cost.booking_id.id
                            invoice_line.booking_line_id = job_cost.booking_line_id.id
                            cost_profit = self.env['freight.cost_profit'].search(
                                [('id', '=', job_cost.booking_line_id.id)], limit=1)

                            vendor_bill_ids_list = []
                            vendor_ids_list = []
                            for cost_profit_vendor_bill_list in cost_profit.vendor_bill_ids:
                                vendor_bill_ids_list.append(cost_profit_vendor_bill_list.id)
                            for cost_profit_vendor_list in cost_profit.vendor_id_ids:
                                vendor_ids_list.append(cost_profit_vendor_list.id)
                            vendor_bill_ids_list.append(invoice.id)
                            vendor_ids_list.append(invoice.partner_id.id)

                            cost_profit.write({
                                'vendor_id_ids': [(6, 0, vendor_ids_list)],
                                'vendor_bill_ids': [(6, 0, vendor_bill_ids_list)],
                            })


                            invoice.write({
                                'freight_booking': booking.id,
                                'account_analytic_id': booking.analytic_account_id.id,
                            })

            booking.action_calculate_cost()

    select_add = fields.Selection([('all', 'Select All'), ('deselect', 'DeSelect All')],
                                  string='Select/DeSelect All to Add to Invoice'
                                  , default='all')

    @api.onchange('select_add')
    def onchange_select_add(self):
        if self.select_add == 'all':
            for cost_profit_line in self.job_cost_lines:
                if cost_profit_line.matched and not cost_profit_line.billed:
                    cost_profit_line.add_to_invoice = True
        elif self.select_add == 'deselect':
            for cost_profit_line in self.job_cost_lines:
                cost_profit_line.add_to_invoice = False


class FreightBookingJobCostLine(models.TransientModel):
    _name = 'job.cost.wizard.line'

    job_cost_id = fields.Many2one('job.cost.wizard', 'Job Cost')
    billed = fields.Boolean(string='Billed')
    add_to_vendor_bill = fields.Boolean(string='Add')
    matched = fields.Boolean(string='Matched')
    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Text(string="Description")
    profit_qty = fields.Float(string='Qty', digits=(12, 2))
    list_price = fields.Float(string="Unit Price")
    profit_amount = fields.Float(string="Amt")
    sale_total = fields.Float(string="Total Sales")
    cost_qty = fields.Integer(string='Qty')
    cost_price = fields.Float(string="Unit Price")
    cost_amount = fields.Float(string="Amt")
    cost_total = fields.Float(string="Total Cost")
    profit_total = fields.Float(string="Total Profit")
    booking_line_id = fields.Many2one('freight.cost_profit')
    booking_id = fields.Many2one('freight.booking')



