from odoo import models, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.multi
    def cron_upload_attachments(self):
        company_id = self.env.user.company_id
        model_ids = [m.model for m in company_id.model_ids]
        attachment_ids = self.search([('res_model', 'in', model_ids), ('type', '=', 'binary')], limit=10)
        for res in attachment_ids:
            active_model = res.res_model
            if active_model in model_ids and res.name != 'thumbnail' and active_model != 'mail.compose.message':
                active_id = res.res_id
                folder = company_id.folder_type
                if folder == 'single_folder':
                    parent_id = company_id.drive_folder_id
                if folder == 'multi_folder':
                    m_folder_id = self.env['multi.folder.drive'].search([
                        ('model_id.model', '=', active_model), ('company_id', '=', company_id.id)], limit=1)
                    parent_id = m_folder_id.folder_id and m_folder_id.folder_id or company_id.drive_folder_id
                if folder == 'record_wise_folder':
                    rec_id = self.env[active_model].browse(active_id)
                    attachment = self.env['ir.attachment'].search([('res_model', '=', active_model), ('res_id', '=', active_id), ('folder_id', '!=', False), ('company_id', '=', company_id.id)])
                    if not attachment:
                        parent_id = self.create_folder_on_google_drive(rec_id.name and rec_id.name or res.res_name, active_model)
                        res.folder_id = parent_id
                    else:
                        parent_id = attachment.folder_id
                if parent_id:
                    file_url = self.env['google.file.upload'].upload_to_google_drive(
                        res.name, res.datas, parent_id)
                    if file_url:
                        res.datas = False
                        res.type = 'url'
                        res.url = file_url.get('url')
                        res.file_id = file_url.get('file_id')
                        self.env['ir.attachment']._file_gc()
