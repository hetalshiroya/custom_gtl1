# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo.osv.expression import OR
import logging
_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):

    #Pass data to breadcrumb
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # domain is needed to hide non portal project for employee
        # portal users can't see the privacy_visibility, fetch the domain for them in sudo
        # si_count = request.env['freight.website.si'].search_count(
        #     [('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #      ('si_status', 'in', ['01', '02'])])
        # si_count = request.env['freight.website.si'].search_count(
        #   [('commercial_partner_id', 'in', [partner]),
        #     ('si_status', 'in', ['01', '02'])])
        #('commercial_partner_id', 'in', [user.partner_id.id])
        si_count = request.env['freight.website.si'].search_count([('si_status', 'in', ['01', '02'])])
        #print('si_count=' + str(si_count))
        #request.env.user.has_group('website.group_website_designer')
        #commercial partner id = parent
        # quotation_count = SaleOrder.search_count([
        #     ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sent', 'cancel'])
        # ])
        values.update({
            'si_count': si_count,
        })
        return values

    #pass data for SI table
    @http.route(['/my/si', '/my/si/page/<int:page>'], type='http', auth="user", website=True)
    def my_si(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        groupby = 'none'  # kw.get('groupby', 'project') #TODO master fix this
        values = self._prepare_portal_layout_values()
        owner = request.env.user.id
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'status': {'label': _('Status'), 'order': 'si_status'},
        }
#         searchbar_filters = {
#             'all': {'label': _('All'), 'domain': []},
#         }
#         searchbar_inputs = {
#             'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
#             'message': {'input': 'message', 'label': _('Search in Messages')},
# #            'customer': {'input': 'customer', 'label': _('Search in Customer')},
#             'stage': {'input': 'stage', 'label': _('Search in Stages')},
#             'all': {'input': 'all', 'label': _('Search in All')},
#         }
#         searchbar_groupby = {
#             'none': {'input': 'none', 'label': _('None1')},
#             'project': {'input': 'project', 'label': _('Project')},
#         }

        # domain = [
        #     ('create_uid', '=', [owner]),
        # ]
        domain = [
            ('si_status', 'in', ['01', '02']),
        ]

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        # if not filterby:
        #     filterby = 'all'
        # domain += searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('freight.website.si', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        # if search and search_in:
        #     search_domain = []
        #     # if search_in in ('content', 'all'):
        #     #     search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
        #     if search_in in ('customer', 'all'):
        #         search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
        #     # if search_in in ('message', 'all'):
        #     #     search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
        #     # if search_in in ('stage', 'all'):
        #     #     search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
        #     domain += search_domain

        # count for pager
        si_count = request.env['freight.website.si'].search_count(domain)

        pager = request.website.pager(
            url="/my/si",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=si_count,
            page=page,
            step=self._items_per_page
        )

        # count for pager
        #quotation_count = SaleOrder.search_count(domain)
        # make pager

        # content according to pager and archive selected
        sis = request.env['freight.website.si'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'sortby': sortby,
            'sis': sis.sudo(),
            'page_name': 'si',
            'archive_groups': archive_groups,
            'default_url': '/my/si',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("sci_goexcel_freight.portal_my_si", values)

    #pass data to each individual SI
    @http.route(['/my/si/<int:si_id>'], type='http', auth="user", website=True)
    def my_sis_si(self, si_id=None, **kw):
        si = request.env['freight.website.si'].browse(si_id)
        return request.render("sci_goexcel_freight.my_si_si", {'si': si})


    #edit a SI
    @http.route('/my/si/edit/<int:si_id>', type="http", auth="user", website=True)
    def si_submit_new(self, si_id=None, **kw):
        si = request.env['freight.website.si'].browse(si_id)
        vals = {
            #'create_uid': request.env.user.id,
            'si': si,
        }
        return request.render('sci_goexcel_freight.new_si_edit', vals)


    #Update a SI
    @http.route(['/my/si/process'], type='http', auth='user', methods=['POST'], website=True)
    def si_update(self, **post):
        si_id = int(request.params.get('id'))
        si = request.env['freight.website.si'].browse(si_id)
        #print('BOL Type=' + str(request.params.get('bill_of_lading_type')))
        si_val = {
            #'cargo_type': request.params.get('cargo_type'),
            #'service_type': self.service_type or False,
            'booking_date': request.params.get('booking_date'),
            #'customer_name': self.customer_name.id or False,
            'shipper': request.params.get('shipper'),
            'consignee': request.params.get('consignee'),
            'notify_party': request.params.get('notify_party'),
            # 'billing_address': self.customer_name.id or False,
            #'booking_ref': self.id,
            'carrier_booking_ref': request.params.get('carrier_booking_ref'),
            'voyage_no': request.params.get('voyage_no'),
            'vessel': request.params.get('vessel'),
            'port_of_loading_input': request.params.get('port_of_loading_input'),
            'port_of_discharge_input': request.params.get('port_of_discharge_input'),
            'place_of_delivery': request.params.get('place_of_delivery'),
            'note': request.params.get('note'),
            'shipping_agent': request.params.get('shipping_agent'),
            'si_status': '02',
            'bill_of_lading_type': request.params.get('bill_of_lading_type'),
            'freight_type': request.params.get('freight_type'),
        }
        #values = self._prepare_portal_layout_values()
        #_logger.warning('values=' + str(values))
        if si:
            si.sudo().write(si_val)
            vals = {
                # 'create_uid': request.env.user.id,
                'si': si,
            }
            return request.render('sci_goexcel_freight.new_si_line_edit', vals)
            #return request.redirect('/my/si')


    # Delete a SI FCL line
    @http.route(['/my/si/delete_fcl_line/<int:si_id>/<int:line_id>'], type='http', auth='user', website=True)
    def si_fcl_line_delete(self, si_id=None, line_id=None, **kw):
        si = request.env['freight.website.si'].browse(si_id)
        #_logger.warning('si=' + str(si.id))
        #line = si.fcl_line_ids.filtered(lambda f: f.fcl_line == line_fcl_line)
        for line in si.fcl_line_ids:
            #_logger.warning('line id=' + str(line.id))
            #_logger.warning('line_fcl_line=' + str(line_fcl_line))
            if line.id == int(line_id):
                line.sudo().unlink()

        vals = {
            # 'create_uid': request.env.user.id,
            'si': si,
        }
        return request.render('sci_goexcel_freight.new_si_line_edit', vals)

    # Delete a SI LCL line
    @http.route(['/my/si/delete_lcl_line/<int:si_id>/<int:line_id>'], type='http', auth='user', website=True)
    def si_lcl_line_delete(self, si_id=None, line_id=None, **kw):
        si = request.env['freight.website.si'].browse(si_id)
        # _logger.warning('si=' + str(si.id))
        # line = si.fcl_line_ids.filtered(lambda f: f.fcl_line == line_fcl_line)
        for line in si.lcl_line_ids:
            #_logger.warning('line id=' + str(line.id))
            #_logger.warning('line_fcl_line=' + str(line_fcl_line))
            if line.id == int(line_id):
                line.sudo().unlink()
        vals = {
            # 'create_uid': request.env.user.id,
            'si': si,
        }
        return request.render('sci_goexcel_freight.new_si_line_edit', vals)

    # When click done
    @http.route(['/my/si/done'], type='http', auth='user', methods=['POST'], website=True)
    def si_done(self, **post):
        return request.redirect('/my/si')

    # Add a line (fcl or lcl)
    @http.route(['/my/si/add_line'], type='http', auth='user', methods=['POST'], website=True)
    def si_add_line(self, **post):
        si_id = int(request.params.get('id'))
        si = request.env['freight.website.si'].browse(si_id)
        _logger.warning('si=' + str(si.id))
        _logger.warning('cargo type=' + str(si.cargo_type))
        if si.cargo_type == 'fcl':
            _logger.warning('fcl')
            si_line_obj = request.env['freight.website.si.fcl']
            si_line = si_line_obj.create({
                'container_product_name': request.params.get('container_product_name'),
                'fcl_line': si.id or '',
                'fcl_container_qty': request.params.get('fcl_container_qty'),
                'seal_no': request.params.get('seal_no'),
                # 'customer_name': self.customer_name.id or False,
                'packages_no': request.params.get('packages_no'),
                'exp_gross_weight': request.params.get('exp_gross_weight'),
                'exp_vol': request.params.get('exp_vol'),
                'remark': request.params.get('remark'),
            })
            si.sudo().write({'fcl_line_ids': si_line or False})
        else:
            _logger.warning('lcl')
            si_line_obj = request.env['freight.website.si.lcl']
            si_line = si_line_obj.create({
                'container_product_name': request.params.get('container_product_name'),
                'lcl_line': si.id or '',
                #'fcl_container_qty': request.params.get('fcl_container_qty'),
                # 'customer_name': self.customer_name.id or False,
                'packages_no': request.params.get('packages_no'),
                'exp_gross_weight': request.params.get('exp_gross_weight'),
                'exp_net_weight': request.params.get('exp_net_weight'),
                'dim_length': request.params.get('dim_length'),
                'dim_weight': request.params.get('dim_weight'),
                'dim_height': request.params.get('dim_height'),
                'exp_vol': request.params.get('exp_vol'),
                'shipping_mark': request.params.get('remark'),
            })
            si.sudo().write({'lcl_line_ids': si_line or False})
        # _logger.warning('values=' + str(values))
        if si:
            #si.sudo().write(si_val)
            vals = {
                # 'create_uid': request.env.user.id,
                'si': si,
            }
            return request.render('sci_goexcel_freight.new_si_line_edit', vals)

    @http.route(['/my/si/edit_line'], type='http', auth='user', methods=['POST'], website=True)
    def si_edit_line(self, **post):
        si_id = int(request.params.get('id'))
        si = request.env['freight.website.si'].browse(si_id)
        _logger.warning('si=' + str(si.id))
        line_id = int(request.params.get('line_id'))
        _logger.warning('si line_id=' + str(line_id))
        if si.cargo_type == 'fcl':
            _logger.warning('fcl')
            for line in si.fcl_line_ids:
                if line.id == line_id:
                    line.container_product_name = request.params.get('container_product_name')
                    line.fcl_container_qty = request.params.get('fcl_container_qty')
                    line.seal_no = request.params.get('seal_no')
                    line.packages_no = request.params.get('packages_no')
                    line.exp_gross_weight = request.params.get('exp_gross_weight')
                    line.exp_vol = request.params.get('exp_vol')
                    line.remark = request.params.get('remark')
        else:
            _logger.warning('lcl')
            for line in si.fcl_line_ids:
                if line.id == line_id:
                    line.container_product_name = request.params.get('container_product_name')
                    line.packages_no = request.params.get('packages_no')
                    line.exp_gross_weight = request.params.get('exp_gross_weight')
                    line.exp_net_weight = request.params.get('exp_net_weight')
                    line.dim_length = request.params.get('dim_length')
                    line.dim_weight= request.params.get('dim_weight')
                    line.dim_height = request.params.get('dim_height')
                    line.exp_vol = request.params.get('exp_vol')
                    line.remark = request.params.get('remark')

        # _logger.warning('values=' + str(values))
        if si:
            # si.sudo().write(si_val)
            vals = {
                # 'create_uid': request.env.user.id,
                'si': si,
            }
            return request.render('sci_goexcel_freight.new_si_line_edit', vals)


#    @http.route(['/si/submit'], type='http', auth="public", website=True)
 #    def new_ticket(self, **kw):
 #
 #        if(request.session.uid):
 # #          user = request.env.user
 #            vals = {
 #                'create_uid': request.env.user.id,
 #            }
 #        else:
 #            vals = {
 #                'create_uid': None,
 #            }
 #
 #        return request.render("sci_goexcel_freight.new_si", vals)

    # @http.route(['/si/si_thanks'], type='http', auth="public", website=True)
    # def ticket_thanks(self, **kw):
    #     if (request.session.uid):
    #         #          user = request.env.user
    #         vals = {
    #             'create_uid': request.env.user.id,
    #         }
    #     else:
    #         vals = {
    #             'create_uid': None,
    #         }
    #
    #     return request.render("sci_goexcel_freight.si_thanks", vals)

    # @http.route(['/si'], type='http', auth="public", website=True)
    # def helpdesk(self, **kw):
    #     team = http.request.env.ref('helpdesk_lite.team_alpha')
    #     team.website_published = False
    #     return request.render("helpdesk_lite.helpdesk",{ 'use_website_helpdesk_form' : True,
    #                                                 'team': team,
    #                                                 })
        # teams = http.request.env['helpdesk_lite.team']
        # return request.render("helpdesk_lite.helpdesk",{ 'teams' : teams,
        #                                             'team': team,
        #                                             'use_website_helpdesk_form' : True })

