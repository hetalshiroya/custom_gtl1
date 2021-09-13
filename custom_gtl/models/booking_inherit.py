from odoo import api, fields, models, exceptions
import logging
from odoo.tools import float_round
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    lcl_container = fields.Char(string='Container Qty/Type', track_visibility='onchange')

    bl_status = fields.Selection([('original', 'Original'),
                                  ('seaway', 'Seaway'),
                                  ('telex', 'Telex')],
                                 string="BL Status", track_visibility='onchange')

    billing_on = fields.Selection([('weight', 'Weight'),
                                   ('volume', 'Volume')], string="Billing On",
                                  default='weight', track_visibility='onchange')

    @api.model
    def _get_default_term(self):
        comment = self.env.user.company_id.invoice_note
        return comment

    invoice_term = fields.Text('Term', default=_get_default_term)
    instruction = fields.Text('Instruction')

    @api.onchange('sq_reference')
    def onchange_sq_reference(self):
        if self.sq_reference:
            if not self.booking_no and not self.local_job_no:
                raise ValidationError("Please Save This Booking Job First!")
            sq = self.env['sale.order'].search([('id', '=', self.sq_reference.id)])
            booking = self.env['freight.booking'].search([('booking_no', '=', self.booking_no)], limit=1)
            self.billing_address = sq.partner_id.id or False,
            self.sales_person = sq.user_id.id,
            self.incoterm = sq.incoterm.id or False,
            self.port_of_loading = sq.POL.id or False,
            self.port_of_discharge = sq.POD.id or False,
            self.commodity = sq.commodity.id or False,
            self.payment_term = sq.payment_term_id.id or False,
            if sq.carrier_booking_no:
                self.carrier_booking_no = sq.carrier_booking_no
            self.contact_name = sq.contact_name.id or False,
            self.forwarding_agent_code = sq.forwarding_agent_code.id or False,
            self.hs_code = sq.hs_code.id or False,
            if sq.coo:
                self.coo = True
            else:
                self.coo = False
            if sq.container_qty and sq.container_qty > 0:
                self.container_qty = sq.container_qty
            if sq.container_product_id:
                self.container_product_id = sq.container_product_id.id
            if sq.fumigation:
                self.fumigation = True
            else:
                self.fumigation = False
            if sq.insurance:
                self.insurance = True
            else:
                self.insurance = False
            if sq.cpc:
                self.cpc = True
            else:
                self.cpc = False
            self.warehouse_hours = sq.warehouse_hours.id or False,
            self.airport_departure = sq.airport_departure.id or False,
            self.airport_destination = sq.airport_destination.id or False,
            self.transporter_company = sq.transporter_company.id or False,
            shipper_adr = ''
            consignee_adr = ''
            notify_party_adr = ''
            if sq.shipper:
                shipper_adr += sq.shipper.name + "\n"
                if sq.shipper.street:
                    shipper_adr += sq.shipper.street
                if sq.shipper.street2:
                    shipper_adr += ' ' + sq.shipper.street2
                if sq.shipper.zip:
                    shipper_adr += ' ' + sq.shipper.zip
                if sq.shipper.city:
                    shipper_adr += ' ' + sq.shipper.city
                if sq.shipper.state_id:
                    shipper_adr += ', ' + sq.shipper.state_id.name.upper()
                if sq.shipper.country_id:
                    shipper_adr += ', ' + sq.shipper.country_id.name.upper() + "\n"
                if not sq.shipper.country_id:
                    shipper_adr += "\n"
                if sq.shipper.phone:
                    shipper_adr += 'Phone: ' + sq.shipper.phone
                elif sq.shipper.mobile:
                    shipper_adr += '. Mobile: ' + sq.shipper.mobile
            if sq.consignee:
                consignee_adr += sq.consignee.name + "\n"
                if sq.consignee.street:
                    consignee_adr += sq.consignee.street
                if sq.consignee.street2:
                    consignee_adr += ' ' + sq.consignee.street2
                if sq.consignee.zip:
                    consignee_adr += ' ' + sq.consignee.zip
                if sq.consignee.city:
                    consignee_adr += ' ' + sq.consignee.city
                if sq.consignee.state_id:
                    consignee_adr += ', ' + sq.consignee.state_id.name.upper()
                if sq.consignee.country_id:
                    consignee_adr += ', ' + sq.consignee.country_id.name.upper() + "\n"
                if not sq.consignee.country_id:
                    consignee_adr += "\n"
                if sq.consignee.phone:
                    consignee_adr += 'Phone: ' + sq.consignee.phone
                elif sq.consignee.mobile:
                    consignee_adr += '. Mobile: ' + sq.consignee.mobile
            if sq.partner_id:
                notify_party_adr = sq.partner_id.name + "\n"
                if sq.partner_id.street:
                    notify_party_adr += sq.partner_id.street
                if sq.partner_id.street2:
                    notify_party_adr += ' ' + sq.partner_id.street2
                if sq.partner_id.zip:
                    notify_party_adr += ' ' + sq.partner_id.zip
                if sq.partner_id.city:
                    notify_party_adr += ' ' + sq.partner_id.city
                if sq.partner_id.state_id:
                    notify_party_adr += ', ' + sq.partner_id.state_id.name.upper()
                if sq.partner_id.country_id:
                    notify_party_adr += ', ' + sq.partner_id.country_id.name.upper() + "\n"
                if not sq.partner_id.country_id:
                    notify_party_adr += "\n"
                if sq.partner_id.phone:
                    notify_party_adr += 'Phone: ' + sq.partner_id.phone
                elif sq.partner_id.mobile:
                    notify_party_adr += '. Mobile: ' + sq.partner_id.mobile
            # print(booking)
            booking.write({'direction': sq.mode or False,
                           'customer_name': sq.partner_id.id or False,
                           'cargo_type': sq.type or False,
                           'service_type': sq.service_type,
                           'shipper': sq.shipper.id or False,
                           'consignee': sq.consignee.id or False,
                           'notify_party': sq.partner_id.id or False,
                           'notify_party_address_input': notify_party_adr,
                           'consignee_address_input': consignee_adr,
                           'shipper_address_input': shipper_adr,
                           'instruction': sq.instruction or False,
                           })
            for line in booking.cost_profit_ids:
                line.unlink()
            cost_profit_obj = self.env['freight.cost_profit']
            for line in sq.order_line:
                if line.product_id:
                    if line.freight_foreign_price > 0.0:
                        price_unit = line.freight_foreign_price
                    else:
                        price_unit = line.price_unit
                    cost_profit_line = cost_profit_obj.create({
                        'product_id': line.product_id.id or False,
                        'product_name': line.name or False,
                        'booking_id': booking.id or '',
                        'profit_qty': line.product_uom_qty or 0,
                        'profit_currency': line.freight_currency.id,
                        'profit_currency_rate': line.freight_currency_rate or 1.0,
                        'list_price': price_unit or 0.0,
                    })
                    booking.write({'cost_profit_ids': cost_profit_line or False})

    @api.onchange('obl_no')
    def onchange_obl_no(self):
        if self.obl_no:
            bls = self.env['freight.bol'].search([('booking_ref', '=', self._origin.id)])
            for bl in bls:
                bl.write({'hbl_no': self.obl_no})

    ## Canon Start ##
    def action_create_bl(self):
        if self.service_type == 'ocean':
            if self.cargo_type == 'fcl':
                container_line = self.operation_line_ids
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    if line.container_product_name and not line.created_bl:
                        bol_obj = self.env['freight.bol']
                        bol_val = {
                            'bol_status': self.bol_status or '01',
                            'no_of_original_bl': self.no_of_original_bl or '0',
                            'direction': self.direction or False,
                            'cargo_type': self.cargo_type or False,
                            'service_type': self.service_type or False,
                            'booking_date': self.booking_date_time,
                            'customer_name': self.customer_name.id or False,
                            'contact_name': self.contact_name.id or False,
                            'shipper': self.shipper_address_input.upper(),
                            'consignee': self.consignee_address_input.upper(),
                            'notify_party': self.notify_party_address_input.upper(),
                            'booking_ref': self.id,
                            'carrier_booking_no': self.carrier_booking_no,
                            'voyage_no': self.voyage_no,
                            'vessel': self.vessel_name.name,
                            'port_of_loading_input': self.port_of_loading.name,
                            'port_of_discharge_input': self.port_of_discharge.name,
                            'port_of_discharge_eta': self.port_of_discharge_eta,
                            'place_of_delivery': self.place_of_delivery,
                            'term': self.payment_term.name,
                            'analytic_account_id': self.analytic_account_id.id or False,
                            'sales_person': self.sales_person.id or False,
                            'shipping_agent_code': self.shipping_agent_code or False,
                            'shipper_c': self.shipper.id or False,
                            'consignee_c': self.consignee.id or False,
                            'notify_party_c': self.notify_party.id or False,
                            'carrier_c': self.carrier.id or False,
                            'commodity1': self.commodity1.id or False,
                        }
                        bol = bol_obj.create(bol_val)
                        bol_line = bol_line_obj.create({
                            'marks': line.remark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            'container_product_id': line.container_product_id.id or False,
                            'seal_no': line.seal_no or '',
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'packages_no_value': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id or '',
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,

                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        line.created_bl = True
            else:
                # _logger.warning('action_copy_to_booking operation_line_ids2')
                container_line = self.operation_line_ids2
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    if line.container_product_name and not line.created_bl:
                        bol_obj = self.env['freight.bol']
                        bol_val = {
                            'bol_status': self.bol_status or '01',
                            'no_of_original_bl': self.no_of_original_bl or '0',
                            'direction': self.direction or False,
                            'cargo_type': self.cargo_type or False,
                            'service_type': self.service_type or False,
                            'booking_date': self.booking_date_time,
                            'customer_name': self.customer_name.id or False,
                            'contact_name': self.contact_name.id or False,
                            'shipper': self.shipper_address_input.upper(),
                            'consignee': self.consignee_address_input.upper(),
                            'notify_party': self.notify_party_address_input.upper(),
                            'booking_ref': self.id,
                            'carrier_booking_no': self.carrier_booking_no,
                            'voyage_no': self.voyage_no,
                            'vessel': self.vessel_name.name,
                            'port_of_loading_input': self.port_of_loading.name,
                            'port_of_discharge_input': self.port_of_discharge.name,
                            'place_of_delivery': self.place_of_delivery,
                            'term': self.payment_term.name,
                            'analytic_account_id': self.analytic_account_id.id or False,
                            'sales_person': self.sales_person.id or False,
                            'shipping_agent_code': self.shipping_agent_code or False,
                            'shipper_c': self.shipper.id or False,
                            'consignee_c': self.consignee.id or False,
                            'notify_party_c': self.notify_party.id or False,
                            'carrier_c': self.carrier.id or False,
                            'commodity1': self.commodity1.id or False,
                        }
                        bol = bol_obj.create(bol_val)
                        print(bol)
                        bol_line = bol_line_obj.create({
                            'marks': line.shipping_mark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            # 'seal_no': line.seal_no or '',
                            # 'container_product_name': line.freight_currency.id,
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,
                            # 'remark_line': line.remark or '',
                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        line.created_bl = True

        else:
            raise exceptions.ValidationError('BL Creation is only for Ocean Export Freight Booking Job!!!')

    def action_create_bl(self):
        # _logger.warning('action_create_si')
        if self.service_type == 'ocean':
            # _logger.warning('export and ocean')
            # _logger.warning('si id=' + str(si.id))
            if self.cargo_type == 'fcl':
                # _logger.warning('si fcl')
                container_line = self.operation_line_ids
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    if line.container_product_name and not line.created_bl:
                        bol_obj = self.env['freight.bol']
                        bol_val = {
                            'bol_status': self.bol_status or '01',
                            'no_of_original_bl': self.no_of_original_bl or '0',
                            'direction': self.direction or False,
                            'cargo_type': self.cargo_type or False,
                            'service_type': self.service_type or False,
                            'booking_date': self.booking_date_time,
                            'customer_name': self.customer_name.id or False,
                            'contact_name': self.contact_name.id or False,
                            'shipper': self.shipper_address_input.upper(),
                            'consignee': self.consignee_address_input.upper(),
                            'notify_party': self.notify_party_address_input.upper(),
                            'booking_ref': self.id,
                            'carrier_booking_no': self.carrier_booking_no,
                            'voyage_no': self.voyage_no,
                            'vessel': self.vessel_name.name,
                            'port_of_loading_input': self.port_of_loading.name,
                            'port_of_discharge_input': self.port_of_discharge.name,
                            'port_of_discharge_eta': self.port_of_discharge_eta,
                            'place_of_delivery': self.place_of_delivery,
                            'term': self.payment_term.name,
                            'analytic_account_id': self.analytic_account_id.id or False,
                            'sales_person': self.sales_person.id or False,
                            'shipping_agent_code': self.shipping_agent_code or False,
                            'shipper_c': self.shipper.id or False,
                            'consignee_c': self.consignee.id or False,
                            'notify_party_c': self.notify_party.id or False,
                            'carrier_c': self.carrier.id or False,
                            'commodity1': self.commodity1.id or False,
                        }
                        bol = bol_obj.create(bol_val)
                        print(bol)
                        bol_line = bol_line_obj.create({
                            'marks': line.remark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            'container_product_id': line.container_product_id.id or False,
                            'seal_no': line.seal_no or '',
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'packages_no_value': line.packages_no or '',
                            'packages_no_uom': line.packages_no_uom.id or '',
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,

                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        line.created_bl = True
            else:
                # _logger.warning('action_copy_to_booking operation_line_ids2')
                container_line = self.operation_line_ids2
                bol_line_obj = self.env['freight.bol.cargo']
                for line in container_line:
                    if line.container_product_name and not line.created_bl:
                        bol_obj = self.env['freight.bol']
                        bol_val = {
                            'bol_status': self.bol_status or '01',
                            'no_of_original_bl': self.no_of_original_bl or '0',
                            'direction': self.direction or False,
                            'cargo_type': self.cargo_type or False,
                            'service_type': self.service_type or False,
                            'booking_date': self.booking_date_time,
                            'customer_name': self.customer_name.id or False,
                            'contact_name': self.contact_name.id or False,
                            'shipper': self.shipper_address_input.upper(),
                            'consignee': self.consignee_address_input.upper(),
                            'notify_party': self.notify_party_address_input.upper(),
                            'booking_ref': self.id,
                            'carrier_booking_no': self.carrier_booking_no,
                            'voyage_no': self.voyage_no,
                            'vessel': self.vessel_name.name,
                            'port_of_loading_input': self.port_of_loading.name,
                            'port_of_discharge_input': self.port_of_discharge.name,
                            'place_of_delivery': self.place_of_delivery,
                            'term': self.payment_term.name,
                            'analytic_account_id': self.analytic_account_id.id or False,
                            'sales_person': self.sales_person.id or False,
                            'shipping_agent_code': self.shipping_agent_code or False,
                            'shipper_c': self.shipper.id or False,
                            'consignee_c': self.consignee.id or False,
                            'notify_party_c': self.notify_party.id or False,
                            'carrier_c': self.carrier.id or False,
                            'commodity1': self.commodity1.id or False,
                        }
                        bol = bol_obj.create(bol_val)
                        print(bol)
                        bol_line = bol_line_obj.create({
                            'marks': line.shipping_mark or '',
                            'container_product_name': line.container_product_name or False,
                            'cargo_line': bol.id or '',
                            'container_no': line.container_no or '',
                            # 'seal_no': line.seal_no or '',
                            # 'container_product_name': line.freight_currency.id,
                            'packages_no': str(line.packages_no) + ' ' + str(line.packages_no_uom.name),
                            'exp_gross_weight': str(line.exp_gross_weight) or 0.0,
                            'exp_vol': str(line.exp_vol) or 0.0,
                            # 'remark_line': line.remark or '',
                        })
                        bol.write({'cargo_line_ids': bol_line or False})
                        line.created_bl = True

        else:
            raise exceptions.ValidationError('BL Creation is only for Ocean Export Freight Booking Job!!!')

    @api.onchange('shipper')
    def onchange_shipper(self):
        adr = ''
        if self.shipper:
            adr += self.shipper.name + "\n"
            if self.shipper.street:
                adr += self.shipper.street
            if self.shipper.street2:
                adr += ' ' + self.shipper.street2
            if self.shipper.zip:
                adr += ' ' + self.shipper.zip
            if self.shipper.city:
                adr += ' ' + self.shipper.city
            if self.shipper.state_id:
                adr += ', ' + self.shipper.state_id.name.upper()
            if self.shipper.country_id:
                adr += ', ' + self.shipper.country_id.name.upper() + "\n"
            if not self.shipper.country_id:
                adr += "\n"
            if self.shipper.phone:
                adr += 'Phone: ' + self.shipper.phone
            elif self.shipper.mobile:
                adr += '. Mobile: ' + self.shipper.mobile
            self.shipper_address_input = adr

    @api.onchange('consignee')
    def onchange_consignee(self):
        adr = ''
        if self.consignee:
            adr += self.consignee.name + "\n"
            if self.consignee.street:
                adr += self.consignee.street
            if self.consignee.street2:
                adr += ' ' + self.consignee.street2
            if self.consignee.zip:
                adr += ' ' + self.consignee.zip
            if self.consignee.city:
                adr += ' ' + self.consignee.city
            if self.consignee.state_id:
                adr += ', ' + self.consignee.state_id.name.upper()
            if self.consignee.country_id:
                adr += ', ' + self.consignee.country_id.name.upper() + "\n"
            if not self.consignee.country_id:
                adr += "\n"
            if self.consignee.phone:
                adr += 'Phone: ' + self.consignee.phone
            elif self.consignee.mobile:
                adr += '. Mobile: ' + self.consignee.mobile
            # if self.consignee.country_id:
            #     adr += ', ' + self.consignee.country_id.name
            # _logger.warning("adr" + adr)
            self.consignee_address_input = adr
        if self.direction:
            if self.direction == 'export':
                self.notify_party = self.consignee.id

    @api.onchange('notify_party')
    def onchange_notify_party(self):
        adr = ''
        if self.notify_party:
            adr = self.notify_party.name + "\n"
            if self.notify_party.street:
                adr += self.notify_party.street
            if self.notify_party.street2:
                adr += ' ' + self.notify_party.street2
            if self.notify_party.zip:
                adr += ' ' + self.notify_party.zip
            if self.notify_party.city:
                adr += ' ' + self.notify_party.city
            if self.notify_party.state_id:
                adr += ', ' + self.notify_party.state_id.name.upper()
            if self.notify_party.country_id:
                adr += ', ' + self.notify_party.country_id.name.upper() + "\n"
            if not self.notify_party.country_id:
                adr += "\n"
            if self.notify_party.phone:
                adr += 'Phone: ' + self.notify_party.phone
            elif self.notify_party.mobile:
                adr += '. Mobile: ' + self.notify_party.mobile

            # if self.notify_party.country_id:
            #     adr += ', ' + self.notify_party.country_id.name
            # _logger.warning("adr" + adr)
            self.notify_party_address_input = adr

    ## Canon End ##

    ## TS - generate report  ##
    booking_invoice_lines_ids = fields.One2many('booking.invoice.line', 'booking_id', string="Booking Invoices",
                                                copy=True, auto_join=True, track_visibility='always')
    inv_sales = fields.Float(string='Inv. Sales')
    inv_cost = fields.Float(string='Inv. Cost')
    inv_profit = fields.Float(string='Inv. Profit')
    diff_amount = fields.Float(string='Diff. Sales Amount')
    diff_cost_amount = fields.Float(string='Diff. Cost Amount')
    pivot_sale_total = fields.Float(string='Total Sales', compute="_compute_pivot_sale_total_new", store=True)
    pivot_cost_total = fields.Float(string='Total Cost', compute="_compute_pivot_cost_total_new", store=True)
    pivot_profit_total = fields.Float(string='Total Profit', compute="_compute_pivot_profit_total_new", store=True)
    pivot_margin_total = fields.Float(string='Margin %', compute="_compute_pivot_margin_total_new", digit=(8, 2),
                                      store=True, group_operator="avg")

    # @api.multi
    # def _get_default_container_category(self):
    #     print('>>>>>>>>>>> _get_default_container_category')
    #     container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
    #     for container_line in container_lines:
    #         print('>>>>>>>>>>>>>>> _get_default_container_category', container_line.product_category.name)
    #         return container_line.product_category
    #
    # container_category_id = fields.Many2one('product.category', string="Container Product Id",
    #                                         default=_get_default_container_category)
    container_qty = fields.Float(string="Ctnr Qty", digits=(8, 0), track_visibility='onchange', default=0)
    container_product_id = fields.Many2one('product.product', string='Container Type', track_visibility='onchange')

    @api.onchange('operation_line_ids')
    def _onchange_operation_line_ids(self):
        count = 0
        for operation_line in self.operation_line_ids:
            count += 1
            if not operation_line.container_product_id:
                if self.container_product_id:
                    operation_line.container_product_id = self.container_product_id.id
                    # operation_line.write({'container_product_id': self.container_product_id.id, })
            else:
                if not self.container_product_id:
                    self.container_product_id = operation_line.container_product_id.id
            if self.cargo_type == 'fcl':
                # self.write({'container_qty': count,})
                self.container_qty = count


    @api.onchange('pivot_sale_total', 'pivot_cost_total')
    def _onchange_cost_profit(self):
        self.action_reupdate_booking_invoice_one()


    @api.multi
    def action_reupdate_booking_invoice_one(self):
        #print('>>>>>>action_reupdate_booking_invoice_one')
        # date = datetime.now() + timedelta(days=-70)
        # bookings = self.env['freight.booking'].search([
        #     ('booking_date_time', '>=', date),
        # ])
        for operation in self:
            if operation.booking_no:
                bookings = self.env['freight.booking'].search([
                    ('id', '=', operation.id),
                ])

                #print('>>>>>>action_reupdate_booking_invoice bookings=', len(bookings))
                sorted_recordset = bookings.sorted(key=lambda r: r.id, reverse=True)
                for booking in sorted_recordset:
                    # Get the invoices for booking
                    invoices = self.env['account.invoice'].search([
                        ('freight_booking', '=', booking.id),
                        ('type', 'in', ['out_invoice', 'out_refund']),
                        ('state', '!=', 'cancel'),
                    ])
                    self.env['booking.invoice.line'].search([
                        ('booking_id', '=', booking.id),
                    ]).unlink()

                    if invoices:
                        for invoice in invoices:
                            self.action_create_invoice_line(invoice, booking)
                    vendor_bill_list = []
                    # Get the vendor bills for booking
                    for cost_profit_line in booking.cost_profit_ids:
                        for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                            if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                                vendor_bill_list.append(vendor_bill_line.id)

                    # get the HBL and its invoices
                    hbls = self.env['freight.bol'].search([
                        ('booking_ref', '=', booking.id),
                    ])
                    if hbls:
                        print('>>>>>>>>> action_reupdate_booking_invoice hbl=', len(hbls))
                    for hbl in hbls:
                        hbl_invoices = self.env['account.invoice'].search([
                            ('freight_hbl', '=', hbl.id),
                            ('type', 'in', ['out_invoice', 'out_refund']),
                            ('state', '!=', 'cancel'),
                        ])
                        if hbl_invoices:
                            for invoice in hbl_invoices:
                                self.action_create_invoice_line(invoice, booking)
                        # for hbl_cost_profit_line in hbl.cost_profit_ids:
                        #     for vendor_bill_line in hbl_cost_profit_line.vendor_bill_ids:
                        #         if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        #             vendor_bill_list.append(vendor_bill_line.id)

                    # vb_hbls = self.env['account.invoice'].search([
                    #     ('freight_booking', '=', booking.id),
                    #     ('type', 'in', ['in_invoice', 'in_refund']),
                    #     ('state', '!=', 'cancel'),
                    # ])

                    unique_vendor_bill_list = []
                    for i in vendor_bill_list:
                        if i not in unique_vendor_bill_list:
                            unique_vendor_bill_list.append(i)

                    vbs = self.env['account.invoice'].search([
                        ('freight_booking', '=', booking.id),
                        ('type', 'in', ['in_invoice', 'in_refund']),
                        ('state', '!=', 'cancel'),
                    ])
                    # print('>>>>>>>>>>> _compute_invoices_numbers vendor bills')
                    invoice_name_list = []
                    for x in vbs:
                        invoice_name_list.append(x.id)

                    unique_list = []

                    for y in unique_vendor_bill_list:
                        # inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
                        if invoice_name_list and len(invoice_name_list) > 0:
                            if y not in invoice_name_list:
                                unique_list.append(y)
                                # self.action_create_invoice_line(inv, operation)
                        else:
                            unique_list.append(y)
                            # self.action_create_invoice_line(inv, operation)
                    for z in invoice_name_list:
                        # if z not in vendor_bill_list:
                        unique_list.append(z)
                    for k in unique_list:
                        inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
                        if inv:
                            # print('>>>>>>>>>> Write create vendor bills')
                            self.action_create_invoice_line(inv, booking)
                    #HBL Vendor Bill
                    for hbl in hbls:
                        # Get from the vendor bill list
                        vendor_bill_list = []
                        for cost_profit_line in hbl.cost_profit_ids:
                            for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                                if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                                    vendor_bill_list.append(vendor_bill_line.id)

                        invoices = self.env['account.invoice'].search([
                            ('freight_hbl', '=', hbl.id),
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
                        for k in unique_list:
                            inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
                            if inv:
                                # print('>>>>>>>>>> Write create vendor bills')
                                self.action_create_invoice_line(inv, booking)
                    # TODO purchase receipt
                    pr_lines = self.env['account.voucher.line'].search([
                        ('freight_booking', '=', booking.id),
                    ])
                    #pr_list = []
                    amt = 0.00
                    reference = ''
                    invoice_no = ''
                    for pr_line in pr_lines:
                        if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                            #pr_list.append(pr_line.voucher_id.id)
                            job_no = ''
                            if pr_line.freight_booking:
                                job_no = pr_line.freight_booking.booking_no
                            elif pr_line.freight_hbl:
                                job_no = pr_line.freight_hbl.bol_no
                            amt += pr_line.price_subtotal
                            invoice_no = pr_line.voucher_id.number
                            reference = pr_line.voucher_id.reference

                    if amt > 0 or amt < 0:
                        # print('>>>>> create vb invoice_line')
                        invoice_line = self.env['booking.invoice.line']
                        invoice_line_1 = invoice_line.create({
                            'invoice_no': invoice_no or '',
                            'reference': reference or '',
                            'invoice_amount': amt or 0,
                            'type': 'purchase_receipt',
                            'booking_id': booking.id or False,
                            'job_no': job_no or '',
                        })

                    # Inv sales and Cost is only for booking is only for booking job and purchase receipt (not HBL)
                    booking_invoice_lines = self.env['booking.invoice.line'].search([('booking_id', '=', booking.id)])
                    inv_sales = 0
                    inv_cost = 0
                    for booking_invoice_line in booking_invoice_lines:
                        if booking_invoice_line.type in ['out_invoice', 'out_refund']:
                            inv_sales += booking_invoice_line.invoice_amount
                        if booking_invoice_line.type in ['in_invoice', 'in_refund', 'purchase_receipt']:
                            inv_cost += booking_invoice_line.invoice_amount

                    booking.write({'inv_sales': inv_sales,
                                   'inv_cost': inv_cost})

                    profit = inv_sales - inv_cost
                    # booking.inv_profit = float_round(profit, 2, rounding_method='HALF-UP')
                    booking.write({'inv_profit': float_round(profit, 2, rounding_method='HALF-UP'), })




    @api.multi
    def action_reupdate_booking_invoice(self):
        date = datetime.now() + timedelta(days=-70)
        bookings = self.env['freight.booking'].search([
            ('booking_date_time', '>=', date),
        ])
        for operation in self:
            bookings = self.env['freight.booking'].search([
                ('id', '=', operation.id),
            ])
        # print('>>>>>>action_reupdate_booking_invoice bookings=', len(bookings))
        sorted_recordset = bookings.sorted(key=lambda r: r.id, reverse=True)
        for booking in sorted_recordset:
            # Get the invoices for booking
            invoices = self.env['account.invoice'].search([
                ('freight_booking', '=', booking.id),
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', '!=', 'cancel'),
            ])
            self.env['booking.invoice.line'].search([
                ('booking_id', '=', booking.id),
            ]).unlink()

            if invoices:
                for invoice in invoices:
                    self.action_create_invoice_line(invoice, booking)
            vendor_bill_list = []
            # Get the vendor bills for booking
            for cost_profit_line in booking.cost_profit_ids:
                for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                    if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                        vendor_bill_list.append(vendor_bill_line.id)

            # get the HBL and its invoices
            hbls = self.env['freight.bol'].search([
                ('booking_ref', '=', booking.id),
            ])
            if hbls:
                print('>>>>>>>>> action_reupdate_booking_invoice hbl=', len(hbls))
            for hbl in hbls:
                hbl_invoices = self.env['account.invoice'].search([
                    ('freight_hbl', '=', hbl.id),
                    ('type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '!=', 'cancel'),
                ])
                if hbl_invoices:
                    for invoice in hbl_invoices:
                        self.action_create_invoice_line(invoice, booking)
                # for hbl_cost_profit_line in hbl.cost_profit_ids:
                #     for vendor_bill_line in hbl_cost_profit_line.vendor_bill_ids:
                #         if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                #             vendor_bill_list.append(vendor_bill_line.id)

            # vb_hbls = self.env['account.invoice'].search([
            #     ('freight_booking', '=', booking.id),
            #     ('type', 'in', ['in_invoice', 'in_refund']),
            #     ('state', '!=', 'cancel'),
            # ])

            unique_vendor_bill_list = []
            for i in vendor_bill_list:
                if i not in unique_vendor_bill_list:
                    unique_vendor_bill_list.append(i)

            vbs = self.env['account.invoice'].search([
                ('freight_booking', '=', booking.id),
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('state', '!=', 'cancel'),
            ])
            # print('>>>>>>>>>>> _compute_invoices_numbers vendor bills')
            invoice_name_list = []
            for x in vbs:
                invoice_name_list.append(x.id)

            unique_list = []

            for y in unique_vendor_bill_list:
                # inv = self.env['account.invoice'].search([('id', '=', y)], limit=1)
                if invoice_name_list and len(invoice_name_list) > 0:
                    if y not in invoice_name_list:
                        unique_list.append(y)
                        # self.action_create_invoice_line(inv, operation)
                else:
                    unique_list.append(y)
                    # self.action_create_invoice_line(inv, operation)
            for z in invoice_name_list:
                # if z not in vendor_bill_list:
                unique_list.append(z)
            for k in unique_list:
                inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
                if inv:
                    # print('>>>>>>>>>> Write create vendor bills')
                    self.action_create_invoice_line(inv, booking)
            # HBL Vendor Bill
            for hbl in hbls:
                # Get from the vendor bill list
                vendor_bill_list = []
                for cost_profit_line in hbl.cost_profit_ids:
                    for vendor_bill_line in cost_profit_line.vendor_bill_ids:
                        if vendor_bill_line.type in ['in_invoice', 'in_refund']:
                            vendor_bill_list.append(vendor_bill_line.id)

                invoices = self.env['account.invoice'].search([
                    ('freight_hbl', '=', hbl.id),
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
                for k in unique_list:
                    inv = self.env['account.invoice'].search([('id', '=', k), ('state', '!=', 'cancel')], limit=1)
                    if inv:
                        # print('>>>>>>>>>> Write create vendor bills')
                        self.action_create_invoice_line(inv, booking)
            # TODO purchase receipt
            pr_lines = self.env['account.voucher.line'].search([
                ('freight_booking', '=', booking.id),
            ])
            # pr_list = []
            amt = 0.00
            reference = ''
            invoice_no = ''
            for pr_line in pr_lines:
                if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                    # pr_list.append(pr_line.voucher_id.id)
                    job_no = ''
                    if pr_line.freight_booking:
                        job_no = pr_line.freight_booking.booking_no
                    elif pr_line.freight_hbl:
                        job_no = pr_line.freight_hbl.bol_no
                    amt += pr_line.price_subtotal
                    invoice_no = pr_line.voucher_id.number
                    reference = pr_line.voucher_id.reference

            if amt > 0 or amt < 0:
                # print('>>>>> create vb invoice_line')
                invoice_line = self.env['booking.invoice.line']
                invoice_line_1 = invoice_line.create({
                    'invoice_no': invoice_no or '',
                    'reference': reference or '',
                    'invoice_amount': amt or 0,
                    'type': 'purchase_receipt',
                    'booking_id': booking.id or False,
                    'job_no': job_no or '',
                })

            # Inv sales and Cost is only for booking is only for booking job and purchase receipt (not HBL)
            booking_invoice_lines = self.env['booking.invoice.line'].search([('booking_id', '=', booking.id)])
            inv_sales = 0
            inv_cost = 0
            for booking_invoice_line in booking_invoice_lines:
                if booking_invoice_line.type in ['out_invoice', 'out_refund']:
                    inv_sales += booking_invoice_line.invoice_amount
                if booking_invoice_line.type in ['in_invoice', 'in_refund', 'purchase_receipt']:
                    inv_cost += booking_invoice_line.invoice_amount

            booking.write({'inv_sales': inv_sales,
                           'inv_cost': inv_cost})

            profit = inv_sales - inv_cost
            # booking.inv_profit = float_round(profit, 2, rounding_method='HALF-UP')
            booking.write({'inv_profit': float_round(profit, 2, rounding_method='HALF-UP'), })



    @api.one
    @api.depends('inv_sales')
    def _compute_pivot_sale_total_new(self):
        # _logger.warning('onchange_pivot_sale_total')
        self.pivot_sale_total = self.inv_sales

    @api.one
    @api.depends('inv_cost')
    def _compute_pivot_cost_total_new(self):
        self.pivot_cost_total = self.inv_cost

    @api.one
    @api.depends('inv_profit')
    def _compute_pivot_profit_total_new(self):
        self.pivot_profit_total = self.inv_profit

    @api.one
    @api.depends('pivot_profit_total')
    def _compute_pivot_margin_total_new(self):
        for service in self:
            if service.pivot_sale_total > 0:
                service.pivot_margin_total = (service.pivot_profit_total / service.pivot_sale_total) * 100

    @api.multi
    def action_create_invoice_line(self, invoice, booking):
        job_no = ''
        if invoice.type in ['out_invoice', 'out_refund']:   #customer invoice/CN
            #print('>>>>>> action_create_invoice_line')
            if invoice.freight_booking:
                job_no = invoice.freight_booking.booking_no
            elif invoice.freight_hbl:
                job_no = invoice.freight_hbl.bol_no
            if invoice.amount_total_signed > 0 or invoice.amount_total_signed < 0:
                invoice_line = self.env['booking.invoice.line']
                invoice_line_1 = invoice_line.create({
                    'invoice_no': invoice.number or '',
                    'reference': invoice.number or '',
                    'invoice_amount': invoice.amount_total_signed or 0,
                    'type': invoice.type,
                    'booking_id': booking.id or False,
                    'job_no': job_no or '',
                })
                # print('>>>>>write invoice successful')
        elif invoice.type in ['in_invoice', 'in_refund']:
            # print('>>>>>write action_create_invoice_line vendor bill')
            booking_id = False
            if invoice.freight_booking:
                job_no = invoice.freight_booking.booking_no
            elif invoice.freight_hbl:
                job_no = invoice.freight_hbl.bol_no

            # print('>>>>>write vendor bill booking amount:', invoice.amount_total_signed)
            invoice_line = self.env['booking.invoice.line']
            invoice_line_1 = invoice_line.create({
                'invoice_no': invoice.number or '',
                'reference': invoice.reference or '',
                'invoice_amount': invoice.amount_total_signed or 0,
                'type': invoice.type,
                'booking_id': booking.id or False,
                'job_no': job_no or '',
            })
                # print('>>>>>write vendor bill successful')
            if not invoice.freight_booking and not invoice.freight_hbl:
                filtered_inv_lines = invoice.invoice_line_ids.filtered(lambda r: r.freight_booking.id == booking.id)
                # print('VB No=', invoice.number, ' filtered_inv_lines len=', len(filtered_inv_lines))
                if filtered_inv_lines:
                    sorted_recordset = filtered_inv_lines.sorted(key=lambda r: r.freight_booking)
                    amt = 0
                    count = 0
                    booking_id = False
                    # print('>>>>>>sorted len=', len(sorted_recordset))
                    for line in sorted_recordset:
                        if line.freight_booking:
                            job_no = line.freight_booking.booking_no
                        elif invoice.freight_hbl:
                            job_no = line.freight_hbl.bol_no
                        if line.freight_booking:
                            count += 1
                            # print('>>>>>>line MLO Split booking no=', line.carrier_booking_no)
                            # for inv_line in line.freight_booking.invoice_line_ids:
                            if not booking_id or line.freight_booking.id == booking_id:
                                amt += line.price_subtotal
                                booking_id = line.freight_booking.id
                                # print('>>>>> amt=', amt)
                            elif line.freight_booking.id != booking_id:
                                # print('>>>>> line.freight_booking.id != booking_id')
                                if line.invoice_id.company_id.currency_id != line.invoice_id.currency_id:
                                    if line.invoice_id.exchange_rate_inverse:
                                        amt = amt * line.invoice_id.exchange_rate_inverse
                                        # print('>>>>> amt with exc rate=', amt)
                                invoice_line = self.env['booking.invoice.line']
                                if line.invoice_type in ['in_refund', 'out_refund']:
                                    amt = -(amt)
                            if amt > 0 or amt < 0:
                                # print('>>>>> create vb invoice_line')
                                invoice_line_1 = invoice_line.create({
                                    'invoice_no': line.invoice_id.number or '',
                                    'reference': line.invoice_id.reference or '',
                                    'invoice_amount': amt or 0,
                                    'type': line.invoice_id.type,
                                    'booking_id': booking_id or False,
                                    'job_no': job_no or '',
                                })
                                amt = 0
                                booking_id = False
                            if len(sorted_recordset) == count:
                                if amt > 0 or amt < 0:
                                    # print('>>>>> create vb invoice_line2 count=', count)
                                    if line.invoice_type in ['in_refund', 'out_refund']:
                                        amt = -(amt)
                                    invoice_line = self.env['booking.invoice.line']
                                    invoice_line_1 = invoice_line.create({
                                        'invoice_no': line.invoice_id.number or '',
                                        'reference': line.invoice_id.reference or '',
                                        'invoice_amount': amt or 0,
                                        'type': line.invoice_id.type,
                                        'booking_id': line.freight_booking.id or False,
                                        'job_no': job_no or '',
                                    })
                                    amt = 0
                                    booking_id = False

        # TS - add for Purchase Receipt

    purchase_receipt_count = fields.Integer(string='Purchase Receipt Count', compute='_get_pr_count', copy=False)

    def _get_pr_count(self):
        # get purchase receipt (Account Voucher) on the lines
        for operation in self:
            # Get PR list
            pr_lines = self.env['account.voucher.line'].search([
                ('freight_booking', '=', operation.id),
            ])
            pr_list = []
            for pr_line in pr_lines:
                if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                    pr_list.append(pr_line.voucher_id.id)
            # pr_name_list = []
            # for x in pr_list:
            #     pr_name_list.append(x.id)
            unique_list = []
            for i in pr_list:
                if i not in unique_list:
                    unique_list.append(i)

            if len(unique_list) > 0:
                self.update({
                    'purchase_receipt_count': len(unique_list),
                })

    @api.multi
    def operation_pr(self):
        for operation in self:
            for operation in self:
                # Get PR list
                pr_lines = self.env['account.voucher.line'].search([
                    ('freight_booking', '=', operation.id),
                ])
                pr_list = []
                for pr_line in pr_lines:
                    if pr_line.voucher_id.state != 'cancel' and pr_line.voucher_id.voucher_type == 'purchase':
                        pr_list.append(pr_line.voucher_id.id)
                # pr_name_list = []
                # for x in pr_list:
                #     pr_name_list.append(x.id)
                unique_list = []
                for i in pr_list:
                    if i not in unique_list:
                        unique_list.append(i)

        if len(unique_list) > 1:
            views = [(self.env.ref('account_voucher.view_voucher_tree').id, 'tree'),
                     (self.env.ref('account_voucher.view_purchase_receipt_form').id, 'form')]
            return {
                'name': 'Purchase Receipt',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.voucher',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
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
                'res_model': 'account.voucher',
                'res_id': unique_list[0] or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


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
                        price_after_converted = float_round(vb_line.cost_price * vb_line.cost_currency_rate, 2,
                                                            rounding_method='HALF-UP')
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
                            'freight_currency_rate': float_round(vb_line.cost_currency_rate, 6,
                                                                 rounding_method='HALF-UP') or 1.000000,
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
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')


    # @api.multi
    # def operation_bill(self):
    #     for operation in self:
    #         print('>>>>>>>>> operation bill')
    #         """
    #         invoices = self.env['account.invoice'].search([
    #             ('origin', '=', self.booking_no),
    #             ('type', '=', 'in_invoice'),
    #         ])
    #         """
    #         invoices = self.env['freight.cost_profit'].search([
    #             ('booking_id', '=', operation.id),
    #             ('vendor_bill_id', '!=', False)
    #         ])
    #         invoice_name_list = []
    #         for x in invoices:
    #             invoice_name_list.append(x.vendor_bill_id.id)
    #         unique_list = []
    #         for y in invoice_name_list:
    #             if y not in unique_list:
    #                 unique_list.append(y)
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
    #             'context': "{'default_type': 'in_invoice', 'type': 'in_invoice', 'journal_type': 'purchase'}",
    #             'domain': [('id', 'in', unique_list), ('type', '=', 'in_invoice')],
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
    #     else:
    #         print('operation_bill no VB on header')
    #         vbs_to_view = self.env['account.invoice']
    #         # vendor bill is created manually and assigned the cost by the invoice line
    #         billed_vbs = operation.cost_profit_ids.filtered(lambda r: r.invoiced is True)
    #         print('operation_bill billed_vbs=' + str(len(billed_vbs)))
    #         if billed_vbs:
    #             for billed_vb in billed_vbs:
    #                 invoice_lines = self.env['account.invoice.line'].search([
    #                     ('id', '=', billed_vb.bill_line_id.id),
    #                 ])
    #                 for invoice_line in invoice_lines:
    #                     vbs_to_view |= invoice_line.invoice_id
    #
    #             if vbs_to_view and len(vbs_to_view) > 0:
    #                 views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
    #                          (self.env.ref('account.invoice_supplier_form').id, 'form')]
    #                 return {
    #                     'name': 'Vendor bills',
    #                     'view_type': 'form',
    #                     'view_mode': 'tree,form',
    #                     # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
    #                     'view_id': False,
    #                     'res_model': 'account.invoice',
    #                     'views': views,
    #                     'context': "{'default_type': 'in_invoice', 'type': 'in_invoice', 'journal_type': 'purchase'}",
    #                     'domain': [('id', 'in', vbs_to_view.ids), ('type', '=', 'in_invoice')],
    #                     'type': 'ir.actions.act_window',
    #                     # 'target': 'new',
    #                 }
    #             else:
    #                 # TS - bugs vendor bill not shown in the smart button
    #                 invoices = self.env['account.invoice'].search([
    #                     ('origin', '=', self.booking_no),
    #                     ('type', '=', 'in_invoice'),
    #                     ('state', '!=', 'cancel'),
    #                 ])
    #                 if len(invoices) > 1:
    #                     views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
    #                              (self.env.ref('account.invoice_supplier_form').id, 'form')]
    #                     return {
    #                         'name': 'Vendor bills',
    #                         'view_type': 'form',
    #                         'view_mode': 'tree,form',
    #                         # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
    #                         'view_id': False,
    #                         'res_model': 'account.invoice',
    #                         'views': views,
    #                         'context': "{'default_type': 'in_invoice', 'type': 'in_invoice', 'journal_type': "
    #                                    "'purchase'}",
    #                         'domain': [('id', 'in', invoices.ids), ('type', '=', 'in_invoice')],
    #                         'type': 'ir.actions.act_window',
    #                         # 'target': 'new',
    #                     }
    #                 else:
    #                     # print('in vendor bill length =1')
    #                     return {
    #                         # 'name': self.booking_no,
    #                         'view_type': 'form',
    #                         'view_mode': 'form',
    #                         'res_model': 'account.invoice',
    #                         'res_id': invoices.id or False,  # readonly mode
    #                         #  'domain': [('id', 'in', purchase_order.ids)],
    #                         'type': 'ir.actions.act_window',
    #                         'target': 'popup',  # readonly mode
    #                     }


class BookingInvoiceLines(models.Model):
    _name = "booking.invoice.line"

    # invoice_id = fields.Many2one('account.invoice', string="Invoice")
    invoice_no = fields.Char(string="Invoice No")
    reference = fields.Char(string="Vendor Invoice/Payment Ref.")
    invoice_amount = fields.Float(string="Amount", store=True)
    type = fields.Char(string='Type', help="invoice, vendor bill, customer CN and vendor CN, vendor debit note")
    booking_id = fields.Many2one('freight.booking', string='Booking Reference', required=True, ondelete='cascade',
                                 index=True, copy=False)
    job_no = fields.Char(string="Job No")


class CostProfit(models.Model):
    _inherit = "freight.cost_profit"

    profit_qty = fields.Float(string='Qty', default="1.000", digits=(12, 3))
    cost_qty = fields.Float(string='Qty', default="1.000", digits=(12, 3))
    ##TS END
