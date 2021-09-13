from odoo import models, fields, api


###################
# Config Settings #
###################
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    messages_easy_text_preview = fields.Integer(string="Text preview length")
    messages_easy_color_note = fields.Char(string="Note Background",
                                           help="Background color for internal notes in HTML format (e.g. #fbd78b)")

    # -- Save values
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('cetmix.messages_easy_text_preview',
                          self.messages_easy_text_preview)
        ICPSudo.set_param('cetmix.messages_easy_color_note',
                          self.messages_easy_color_note)

    # -- Read values
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        # Text preview length
        messages_easy_text_preview = ICPSudo.get_param('cetmix.messages_easy_text_preview', default=False)
        if messages_easy_text_preview:
            res.update(messages_easy_text_preview=int(messages_easy_text_preview))

        # Internal note background color
        messages_easy_color_note = ICPSudo.get_param('cetmix.messages_easy_color_note', default=False)
        if messages_easy_color_note:
            res.update(messages_easy_color_note=messages_easy_color_note)

        return res
