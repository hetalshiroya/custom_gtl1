from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

#transient model
class PODSignature(models.TransientModel):

    _name = 'trip.pod.signature'

    # = fields.Many2one('transport.rft', string='RFT Reference')
    pod_signature = fields.Binary(string='Consignee Signature')

    @api.multi
    def action_pod_signature_apply(self):
        # if context.get('load_type') == 'ltl':
            load_type = self.env.context.get('load_type')
            #_logger.warning("context load type:" + str(self.env.context.get('load_type')))
            if load_type == 'ftl':
                #_logger.warning("context active id:" + str(self.env.context.get('trip_id')))
                trip_ftl = self.env['dispatch.trip'].browse(self.env.context.get('trip_id'))
                #_logger.warning("len trip ftl:" + str(len(trip_ftl)))
                for trip in trip_ftl:
                    trip.write({'ftl_pod_signature_attachment': self.pod_signature})
            else:
                trip_ltl_loads = self.env['trip.manifest.line.ltl'].browse(self.env.context.get('active_ids'))
                #_logger.warning("len  trip_ltl_loads:" + str(len(trip_ltl_loads)))
                #_logger.warning("print self:" + str(self))
                for load in trip_ltl_loads:
                    #_logger.warning("in trip_ltl_loads:" + str(load.id))
                    load.write({'pod_signature_attachment': self.pod_signature})


        # else:
            #trip_ftl_loads = self.env['trip.manifest.line'].browse(self.env.context.get('active_id'))
            #_logger.warning("len trip_ftl_loads:" + str(len(trip_ftl_loads)))
           # for load in trip_ftl_loads:
                #_logger.warning("in trip_ftl_loads")
           #     load.write({'pod_signature_attachment': self.pod_signature})





            # load.write({'pod_signature_attachment': self.pod_signature,
            #             'pod_signature_file_name': load.manifest_cn_no,
            #             })




