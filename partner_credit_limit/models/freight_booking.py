from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from datetime import date

class FreightBooking(models.Model):
    _inherit = "freight.booking"

    #credit_check_done = fields.Boolean(string='Credit Check Done?', default=False)

    @api.constrains('pivot_sale_total')
    def onchange_pivot_sale_total(self):
       # _logger.warning('onchange_pivot_sale_total freight booking')
        for booking in self:
            booking.check_credit_limit()


    @api.multi
    def check_credit_limit(self):
        #overdue invoice + open invoice + booking job total sales amount (cost & profit line)
        if self.customer_name:
            if not self.customer_name.over_credit:
                credit_limit = self.customer_name.credit_limit
                invoices_credit = 0
                booking_sales_amount = 0
                #_logger.warning('credit_limit=' + str(credit_limit))
                #
                # child_companies = self.env['res.partner'].search([('parent_id', '=', self.customer_name.id),
                #                                                   '|', ('type', '!=', 'contact'),
                #                                                   ('customer', '=', True),])
                child_companies = self.env['res.partner'].search([('parent_id', '=', self.customer_name.id)
                                                                     ,('customer', '=', True),])
                #_logger.warning('child_companies len=' + str(len(child_companies)))
                # overdue invoices + open invoice for parent and children
                for child in child_companies:
                    #_logger.warning('child=' + str(child.display_name) + ' , type=' + str(child.type) + ' , customer=' + str(child.customer))
                    open_due_invoices = self.env['account.invoice'].search([
                        ('type', '=', 'out_invoice'),
                        ('company_id', '=', self.company_id.id),
                        ('partner_id', '=', child.id),
                        ('state', 'in', ['open', 'draft', 'approve', 'in payment']),
                    ])
                    for invoice in open_due_invoices:
                        # amount = invoice.currency_id.convert(invoice.residual,
                        #                                      invoice.currency_id)
                        #_logger.warning('invoice no=' + str(invoice.number) + ' , residual=' + str(invoice.residual))
                        invoices_credit += invoice.residual

                    confirmed_bookings = self.env['freight.booking'].search([('customer_name', '=', child.id),
                                                                             ('shipment_booking_status', 'not in',
                                                                              ['09', '10'])])
                    # booking job total sales amount
                    #_logger.warning('confirmed_bookings count=' + str(len(confirmed_bookings)))
                    for booking in confirmed_bookings:
                        #_logger.warning('booking no=' + str(booking.booking_no) + ' , pivot_sale_total=' + str(
                         #   booking.pivot_sale_total))
                        booking_sales_amount += booking.pivot_sale_total
                        #_logger.warning('booking_sales_amount=' + str(booking_sales_amount))
                #for parent
                open_due_invoices = self.env['account.invoice'].search([
                    ('type', '=', 'out_invoice'),
                    ('company_id', '=', self.company_id.id),
                    ('partner_id', '=', self.customer_name.id),
                    ('state', 'in', ['open','draft','approve','in payment']),
                ])
                #_logger.warning('open_due_invoices count=' + str(len(open_due_invoices)))
                for invoice in open_due_invoices:
                    # amount = invoice.currency_id.convert(invoice.residual,
                    #                                      invoice.currency_id)
                    #_logger.warning('invoice no=' + str(invoice.number) + ' , residual=' + str(invoice.residual))
                    invoices_credit += invoice.residual
                    #_logger.warning('invoices_credit=' + str(invoices_credit))
                confirmed_bookings = self.env['freight.booking'].search([('customer_name', '=', self.customer_name.id),
                                                               ('shipment_booking_status', 'not in', ['09', '10'])])
                # booking job total sales amount
                #_logger.warning('confirmed_bookings count=' + str(len(confirmed_bookings)))

                for booking in confirmed_bookings:
                    #_logger.warning('booking no=' + str(booking.booking_no) + ' , pivot_sale_total=' + str(booking.pivot_sale_total))
                    booking_sales_amount += booking.pivot_sale_total
                    #_logger.warning('booking_sales_amount=' + str(booking_sales_amount))
                # open credit = overdue invoices + open invoice + confirmed booking
                open_credit = invoices_credit + booking_sales_amount
                #_logger.warning('open_credit=' + str(open_credit))
                exceeded_credit = open_credit - credit_limit
                #_logger.warning('exceeded_credit=' + str(exceeded_credit))
                if exceeded_credit > 0:
                    msg = 'The customer "%s" available credit limit (%s) has been Exceeded' \
                          ' by Amount = %s (Open Credit = %s).\n' \
                          'Either advise your customer to pay the invoice or Allow Over Credit' \
                          ' in the Customer->Sales&Purchases.' \
                          % (self.customer_name.name, credit_limit, exceeded_credit, open_credit)
                    #raise UserError(_('You can not save booking. \n' + msg))
                    raise exceptions.ValidationError('You cannot Create/Save Booking Job! \n' + msg)
                #self._context.get('credit')




