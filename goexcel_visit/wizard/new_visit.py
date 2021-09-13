from odoo import models, fields, api, _
from datetime import datetime, timedelta


class newvisit(models.TransientModel):
    _name = 'visit.wizard'
    _description = 'Visit Wizard'

    customer_name = fields.Many2one('res.partner', string='Customer', readonly=True)
    contact = fields.Many2one('res.partner', string='Contact', readonly=True)
    sales_person = fields.Many2one('res.users', string="Salesperson", readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    last_visit_remark = fields.Text(string="Last Visit Remark", readonly=True)
    #visit_purpose = fields.Selection([('salescall', 'Sales Call'), ('campaign', 'Campaign')], string="Visit Purpose")
    visit_purpose = fields.Many2one('visit.purpose', string="Visit Purpose")

    visit_planned_start_date_time = fields.Datetime(string='Planned Start Date Time')
    visit_planned_end_date_time = fields.Datetime(string='Planned End Date Time')
    priority = fields.Selection([('0', 'Low'),
                                 ('1', 'Low'),
                                 ('2', 'Normal'),
                                 ('3', 'High'),
                                 ('4', 'Very High')],
                                string='Priority', select=True, default='2')
    visit_id = fields.Char(string='Visit ID', copy=False, readonly=True, index=True)
    destination = fields.Char(string='Destination', copy=False)


    @api.multi
    def create_new_visit(self, vals):
        vals['visit_status'] = '01'
        vals['customer_name'] = self.customer_name.id
        vals['contact'] = self.contact.id
        vals['visit_purpose'] = self.visit_purpose.id
        vals['visit_planned_start_date_time'] = self.visit_planned_start_date_time
        vals['visit_planned_end_date_time'] = self.visit_planned_end_date_time
        vals['sales_person'] = self.sales_person.id
        vals['priority'] = self.priority
        vals['visit_id'] = self.env['ir.sequence'].next_by_code('visit')
        vals['company_id'] = self.company_id.id
        vals['last_visit_remark'] = self.last_visit_remark
        vals['destination'] = self.destination

        new_id = self.env['visit'].sudo().create(vals)


    @api.onchange('visit_planned_start_date_time')
    def _onchange_visit_planned_start_date_time(self):
        if self.visit_planned_start_date_time:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            visit_planned_start_date_time = datetime.strptime(str(self.visit_planned_start_date_time), DATETIME_FORMAT)
            self.visit_planned_end_date_time = visit_planned_start_date_time + timedelta(minutes=30)



"""


    @api.multi
    def get_distance(self):
        origin = self.origin_address
        destination = self.delivery_address
        maps_selection = self.env["ir.config_parameter"].sudo().get_param("custom_molicc.customer_seal")
        api = self.env["ir.config_parameter"].sudo().get_param("custom_molicc.maps_api")
        if maps_selection == 'bing':
            maps = BingMaps()
        elif maps_selection == 'google':
            maps = GoogleMaps()
        #duration = maps.duration(origin, destination, api)
        distance = maps.distance(origin, destination, api)
        #self.duration = math.ceil(duration / 60)
        distance1 = math.ceil(distance)
        self.price = distance1 * self.number_of_trips * self.price_per_km

        return {
            'name': 'Calculate Delivery Charge',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.charge.wizard',
            'target': 'new',
            'context': {'default_partner_id': self.partner_id.id,
                        'default_origin_address': self.origin_address,
                        'default_delivery_address': self.delivery_address,
                        'default_number_of_trips': self.number_of_trips,
                        'default_price_per_km': self.price_per_km,
                        'default_price': self.price,
                        'default_distance': distance1,
                        'default_sale_order': self.sale_order
                        },
        }

    @api.multi
    def calculate_delivery_charge(self):
        sale_order = self.env['sale.order'].sudo().search([('id', '=', self.sale_order)], limit=1)
        product = self.env["ir.config_parameter"].sudo().get_param("custom_molicc.delivery_charge_product_id")
        product1 = self.env['product.product'].sudo().search([('id', '=', product)], limit=1)
        price = self.distance * self.number_of_trips * self.price_per_km
        if sale_order and product:
            product_lines = []
            line_vals={
                'order_id': sale_order.id,
                'product_id': product1.id,
                'name': product1.name,
                'product_uom_qty': '1',
                'price_unit': price,
            }
            product_lines.append((0,0,line_vals))
            sale_order.order_line = product_lines


"""

