from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Change the display name when user select partner
    # def name_get(self):
    #     res = []
    #     for field in self:
    #         if field.ref:
    #             res.append((field.id, '%s %s' % (field.ref, field.name)))
    #         else:
    #             res.append((field.id, '%s %s' % ('', field.name)))
    #
    #     return res

    #@api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'ref')
    # def _compute_display_name(self):
    #     diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=False)
    #     names = dict(self.with_context(**diff).name_get())
    #     for partner in self:
    #         if partner.ref and len(partner.ref) > 0:
    #             name = names.get(partner.id)
    #             new_name = name.replace(partner.ref, '')
    #             partner.display_name = new_name.strip()
    #         else:
    #             partner.display_name = names.get(partner.id)

    # by default, contact person will also be the customer/vendor (depending on their company)
    # @api.multi
    # def _get_default_is_customer(self):
    #     for contact in self:
    #         if contact.type == 'delivery' or contact.type == 'other' or contact.type == 'private':
    #             return False
    #         elif contact.is_company is False:
    #             return False
    #         else:
    #             return True
    #
    # customer = fields.Boolean(string='Is a Customer', default=_get_default_is_customer,
    #                           help="Check this box if this contact is a customer.")
    #
    # @api.multi
    # def _get_default_is_vendor(self):
    #     for contact in self:
    #         if contact.type == 'delivery' or contact.type == 'other' or contact.type == 'private':
    #             return False
    #         elif contact.is_company is False:
    #             return False
    #         else:
    #             return True
    #
    # supplier = fields.Boolean(string='Is a Vendor', default=_get_default_is_vendor,
    #                           help="Check this box if this contact is a customer.")

    @api.model
    def create(self, vals):
        if vals.get('company_type') == 'person' or vals.get('is_company'):
            vals['customer'] = False
            vals['supplier'] = False

        res = super(ResPartner, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if self.company_type == 'person' and self.parent_id:
            vals['customer'] = False
            vals['supplier'] = False

        res = super(ResPartner, self).write(vals)
        return res