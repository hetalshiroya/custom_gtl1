from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    # Header
    sq_booking_count = fields.Integer(compute='_compute_sq_booking_count')
    contact_name = fields.Many2one('res.partner', string='Contact Name', track_visibility='onchange')
    sq_description = fields.Char(string='SQ Description', track_visibility='onchange')
    incoterm = fields.Many2one('freight.incoterm', string='Incoterm', track_visibility='onchange')
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')], string="Shipment Mode",
                                    default="ocean", track_visibility='onchange')
    mode = fields.Selection([('import', 'Import'), ('export', 'Export'), ('local', 'Local')], string="Mode", default="import", track_visibility='onchange')
    commodity = fields.Many2one('product.product', string='Commodity', track_visibility='onchange')
    commodity1 = fields.Many2one('freight.commodity1', string='Commodity', track_visibility='onchange')
    show_subtotal = fields.Boolean('Show Subtotal', default=True)
    split_signature = fields.Boolean('Split Signature')

    # Ocean
    type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', default="fcl", track_visibility='onchange')
    POL = fields.Many2one('freight.ports', string='Port of Loading', track_visibility='onchange')
    POD = fields.Many2one('freight.ports', string='Port of Discharge', track_visibility='onchange')

    # Air
    airport_departure = fields.Many2one("freight.airport", string='Airport Departure')
    airport_destination = fields.Many2one("freight.airport", string='Airport Destination')
    gross_weight = fields.Float(string="Gross Weight", default=0)
    pallet_dimension = fields.Text(string="Pallet Dimension")
    airlines_ids = fields.Many2many('freight.airlines', string='Airlines')
    weight_ids = fields.Many2many('freight.airlines.weight', string='Weight', limit=3)
    airlines_weight_ids = fields.Many2many('freight.airlines.info', string='Airlines Info')
    airline_line_ids = fields.One2many('freight.airline.line', 'sq_id', string='Airlines Line')

    # Land
    type_of_truck = fields.Many2one('freight.truck', string='Type of Truck',track_visibility='onchange')

    # Booking Note
    carrier_booking_no = fields.Char(string='Carrier Booking No', track_visibility='onchange', copy=False)
    shipper = fields.Many2one('res.partner', string='Shipper', help="The Party who shipped the freight, eg Exporter", track_visibility='onchange')
    consignee = fields.Many2one('res.partner', string='Consignee Name', help="The Party who received the freight", track_visibility='onchange')
    forwarding_agent_code = fields.Many2one('res.partner', string='Forwarding Agent', track_visibility='onchange')
    hs_code = fields.Many2one('freight.hscode', string='HS Code', track_visibility='onchange')
    container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')
    container_qty = fields.Integer(string="Qty", default=0, track_visibility='onchange')
    transporter_company = fields.Many2one('res.partner', string='Transporter Company',
                                          help="The Party who transport the goods from one place to another",
                                          track_visibility='onchange')
    coo = fields.Boolean(string='C.O.O', track_visibility='onchange', help="Certificate Of Origin")
    insurance = fields.Boolean(string='Insurance', track_visibility='onchange')
    fumigation = fields.Boolean(string='Fumigation', track_visibility='onchange')
    cpc = fields.Boolean(string='Container Packing Certificate', track_visibility='onchange')
    warehouse_hours = fields.Many2one('transport.accept.hour', track_visibility='onchange', copy=False)

    @api.multi
    def _get_default_commodity_category(self):
        print('_get_default_commodity_category')
        commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
        print('commodity_lines len=' + str(len(commodity_lines)))
        for commodity_line in commodity_lines:
            _logger.warning('_get_default_commodity_category=' + str(commodity_line.product_category))
            return commodity_line.product_category

    commodity_category_id = fields.Many2one('product.category', string="Commodity Product Id",
                                            default=_get_default_commodity_category)

    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.multi
    def _compute_sq_booking_count(self):
        for sq in self:
            bookings = self.env['freight.booking'].search([
                ('sq_reference', '=', sq.id),
            ])
            sq.sq_booking_count = len(bookings)

    @api.multi
    def action_copy_to_booking(self):
        booking_obj = self.env['freight.booking']
        cost_profit_obj = self.env['freight.cost_profit']
        # fcl_operation_obj = self.env['freight.operations.line']
        # _logger.warning('action_copy_to_booking 1')
        freight_booking_val = {
            'shipment_booking_status': '01',
            'customer_name': self.partner_id.id or False,
            'billing_address': self.partner_id.id or False,
            'sq_reference': self.id,
            'company_id': self.company_id.id,
            'sales_person': self.user_id.id,
            'incoterm': self.incoterm.id or False,
            'direction': self.mode or False,
            'port_of_loading': self.POL.id or False,
            'port_of_discharge': self.POD.id or False,
            'commodity1': self.commodity1.id or False,
            'payment_term': self.payment_term_id.id or False,
            'cargo_type': self.type or False,
            'carrier_booking_no': self.carrier_booking_no,
            'contact_name': self.contact_name.id or False,
            'shipper': self.shipper.id or False,
            'forwarding_agent_code': self.forwarding_agent_code.id or False,
            'consignee': self.consignee.id or False,
            'hs_code': self.hs_code.id or False,
            'coo': self.coo,
            'fumigation': self.fumigation,
            'insurance': self.insurance,
            'cpc': self.cpc,
            'warehouse_hours': self.warehouse_hours.id or False,
            'service_type': self.service_type,
            'airport_departure': self.airport_departure.id or False,
            'airport_destination': self.airport_destination.id or False,
            'transporter_company': self.transporter_company.id or False,
        }
        if self.mode == 'import':
            freight_booking_val = {
                'shipment_booking_status': '01',
                'customer_name': self.partner_id.id or False,
                'billing_address': self.partner_id.id or False,
                'sq_reference': self.id,
                'company_id': self.company_id.id,
                'sales_person': self.user_id.id,
                'incoterm': self.incoterm.id or False,
                'direction': self.mode or False,
                'port_of_loading': self.POL.id or False,
                'port_of_discharge': self.POD.id or False,
                'commodity1': self.commodity1.id or False,
                'payment_term': self.payment_term_id.id or False,
                'cargo_type': self.type or False,
                'carrier_booking_no': self.carrier_booking_no,
                'contact_name': self.contact_name.id or False,
                'shipper': self.shipper.id or False,
                'forwarding_agent_code': self.forwarding_agent_code.id or False,
                'hs_code': self.hs_code.id or False,
                'coo': self.coo,
                'fumigation': self.fumigation,
                'insurance': self.insurance,
                'cpc': self.cpc,
                'warehouse_hours': self.warehouse_hours.id or False,
                'consignee': self.partner_id.id or False,
                'notify_party': self.partner_id.id or False,
                'service_type': self.service_type,
                'airport_departure': self.airport_departure.id or False,
                'airport_destination': self.airport_destination.id or False,
                'transporter_company': self.transporter_company.id or False,
            }

        booking = booking_obj.create(freight_booking_val)
        if booking.service_type == 'air':
            booking.cargo_type = 'lcl'
            booking.land_cargo_type = 'ltl'
        for line in self.order_line:
            # _logger.warning('action_copy_to_booking 1')
            if line.product_id:
                # _logger.warning('action_copy_to_booking 2')

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
                    'tax_id': [(6, 0, line.tax_id.ids)],
                    # 'sale_total': line.price_unit or 0.0,

                })
                # booking.write({'booking_id': booking.id or False,
                #             'cost_profit_ids': cost_profit_line.id or False})
                booking.write({'cost_profit_ids': cost_profit_line or False})

        self.state = 'sale'


    @api.onchange('airlines_ids', 'weight_ids')
    def onchange_airlines(self):
        info_ids = []
        for airline in self.airlines_ids:
            for weight in self.weight_ids:
                info = self.env['freight.airlines.info'].search(
                    [('airline.id', '=', airline.id), ('weight.id', '=', weight.id)])
                if info:
                    info_ids.append(info.id)
        info1 = self.env['freight.airlines.info'].browse(info_ids)
        # self.airlines_weight_ids = info1
        self.airlines_weight_ids = [(6, 0, info_ids)]
        airlines_list = []
        price1_list = []
        price2_list = []
        price3_list = []
        fsc_list = []
        ssc_list = []
        validity_list = []
        routing_frequency_list = []
        dimension_weight_list = []
        weight_list1 = []
        weight_list2 = []
        weight_list3 = []

        for all_airlines in self.airlines_weight_ids:
            if len(airlines_list) == 0:
                airlines_list.append(all_airlines.airline.id)
                price1_list.append(all_airlines.price)
                price2_list.append(0)
                price3_list.append(0)
                fsc_list.append(all_airlines.fsc)
                ssc_list.append(all_airlines.ssc)
                validity_list.append(all_airlines.validity)
                routing_frequency_list.append(all_airlines.routing_frequency)
                if all_airlines.dimension_weight == '0':
                    dimension = '317X240X157cm/4500KG'
                if all_airlines.dimension_weight == '1':
                    dimension = '317X240X299cm/4500KG'
                dimension_weight_list.append(dimension)
                weight_list1.append(all_airlines.weight.weight)
                weight_list2.append(0)
                weight_list3.append(0)
            else:
                check_duplicate = False
                for index, airlines in enumerate(airlines_list):
                    if airlines == all_airlines.airline.id:
                        print(weight_list1[0],weight_list2[0],weight_list3[0])
                        print(all_airlines.weight.weight)
                        check_duplicate = True
                        if weight_list1[0] == all_airlines.weight.weight:
                            price1_list[index] = all_airlines.price
                            print("Weight1")
                        elif price2_list[index] == 0:
                            if all_airlines.weight.weight == weight_list2[0] or weight_list2[0] == 0:
                                price2_list[index] = all_airlines.price
                                weight_list2[0] = all_airlines.weight.weight
                                print("Weight2")
                            else:
                                price3_list[index] = all_airlines.price
                                weight_list3[0] = all_airlines.weight.weight
                                print("Weight2-")
                        elif price3_list[index] == 0:
                            if all_airlines.weight.weight == weight_list3[0] or weight_list3[0] == 0:
                                price3_list[index] = all_airlines.price
                                weight_list3[0] = all_airlines.weight.weight
                                print("Weight3")

                if not check_duplicate:
                    airlines_list.append(all_airlines.airline.id)
                    price1_list.append(all_airlines.price)
                    price2_list.append(0)
                    price3_list.append(0)
                    fsc_list.append(all_airlines.fsc)
                    ssc_list.append(all_airlines.ssc)
                    validity_list.append(all_airlines.validity)
                    routing_frequency_list.append(all_airlines.routing_frequency)
                    if all_airlines.dimension_weight == '0':
                        dimension = '317X240X157cm/4500KG'
                    if all_airlines.dimension_weight == '1':
                        dimension = '317X240X299cm/4500KG'
                    dimension_weight_list.append(dimension)
                    weight_list1.append(all_airlines.weight.weight)
                    weight_list2.append(0)
                    weight_list3.append(0)

        airline_list = []
        for index, airlines in enumerate(airlines_list):
            airline_list.append({
                'airline': airlines_list[index],
                'price1': price1_list[index],
                'price2': price2_list[index],
                'price3': price3_list[index],
                'fsc': fsc_list[index],
                'ssc': ssc_list[index],
                'validity': validity_list[index],
                'routing_frequency': routing_frequency_list[index],
                'dimension_weight': dimension_weight_list[index],
                'price1_weight': weight_list1[0],
                'price2_weight': weight_list2[0],
                'price3_weight': weight_list3[0],
            })

        for rec in self:
            lines = [(5, 0, 0)]
            for index, airlines in enumerate(airlines_list):
                airline1 = self.env['freight.airlines'].browse(airlines_list[index])
                val = {
                    'airline': airline1,
                    'price1': price1_list[index],
                    'price2': price2_list[index],
                    'price3': price3_list[index],
                    'fsc': fsc_list[index],
                    'ssc': ssc_list[index],
                    'validity': validity_list[index],
                    'routing_frequency': routing_frequency_list[index],
                    'dimension_weight': dimension_weight_list[index],
                    'price1_weight': weight_list1[0],
                    'price2_weight': weight_list2[0],
                    'price3_weight': weight_list3[0],
                }
                print(val)
                lines.append((0,0,val))
            rec.airline_line_ids = lines


    @api.onchange('service_type')
    def onchange_service_type(self):
        note = ''
        if self.service_type == 'air':
            note = self.env.user.company_id.air_freight_note
        elif self.service_type == 'land':
            note = self.env.user.company_id.land_freight_note
        else:
            note = self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_sale_note') and self.env.user.company_id.sale_note or ''
        self.note = note

    @api.multi
    def action_send_sq_operation(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_sq', 'email_template_sq_booking_note')[1]

        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }






class SaleQuotationLine(models.Model):
    _inherit = 'sale.order.line'

    freight_currency = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id,
                                        track_visibility='onchange')
    freight_foreign_price = fields.Float(string='Unit Price(FC)', track_visibility='onchange')
    freight_currency_rate = fields.Float(string='Conversion Rate', default="1.00", track_visibility='onchange')
    land_departure = fields.Char(string='Departure', track_visibility='onchange', copy=False)
    land_destination = fields.Char(string='Destination', track_visibility='onchange', copy=False)

    @api.onchange('freight_foreign_price')
    def _onchange_freight_foreign_price(self):
         self.price_unit = self.freight_foreign_price * self.freight_currency_rate or 0.0


    @api.onchange('freight_currency_rate')
    def _onchange_freight_currency_rate(self):
        self.price_unit = self.freight_foreign_price * self.freight_currency_rate or 0.0

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleQuotationLine, self).product_id_change()
        self.name = self.product_id.name
        if self.order_id.service_type == 'land' and self.name :
            if self.order_id.type_of_truck:
                self.name = self.product_id.name + ' - ' + self.order_id.type_of_truck.name
        return res

    #TS - fix bug for conversion when the product_uom_qty has changed.
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            price_unit = self.price_unit
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)
            # TS - fix bug when conversion when the product_uom_qty has changed.
            if self.freight_currency_rate != 1 and self.product_uom_qty:
                self.price_unit = self.freight_foreign_price * self.freight_currency_rate
            # TS - fix bug when quantity changed (without the conversion)
            if price_unit > 0 and self.freight_foreign_price == 1 and self.freight_currency_rate == 1:
                self.price_unit = price_unit


# @api.multi
    # def copy_data(self, default=None):
    #     if
    #     return super(SaleQuotationLine, self).copy(default)
