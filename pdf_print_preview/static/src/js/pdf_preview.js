odoo.define("pdf_print_preview.report", function (require) {
    "use strict";

    var ActionManager = require("web.ActionManager");
    var framework = require("web.framework");
    var session = require("web.session");
    var core = require('web.core');

    var _t = core._t;
    var _lt = core._lt;

    // Messages that will be shown to the user (if needed).
    var WKHTMLTOPDF_MESSAGES = {
        "install": _lt("Unable to find Wkhtmltopdf on this \nsystem. The report will be shown in html.<br><br><a href='http://wkhtmltopdf.org/' target='_blank'>\nwkhtmltopdf.org</a>"),
        "workers": _lt("You need to start OpenERP with at least two \nworkers to print a pdf version of the reports."),
        "upgrade": _lt("You should upgrade your version of\nWkhtmltopdf to at least 0.12.0 in order to get a correct display of headers and footers as well as\nsupport for table-breaking between pages.<br><br><a href='http://wkhtmltopdf.org/' \ntarget='_blank'>wkhtmltopdf.org</a>"),
        "broken": _lt("Your installation of Wkhtmltopdf seems to be broken. The report will be shown in html.<br><br><a href='http://wkhtmltopdf.org/' target='_blank'>wkhtmltopdf.org</a>")
    };

    var PreviewDialog = require("pdf_print_preview.PreviewDialog");

    var wkhtmltopdf_state;

    ActionManager.include({
        _executeReportAction: function (action, options) {
            var self = this;

            if (!session.report_layout || !session.exist_logo) {
                self.do_notify( _t("Report"), _t( "You need to update your company details and upload <b style='color:red;'>your logo</b> to get a beautiful document. <br/> by going to <b style='color:red;'>Settings</b> and Activate the developer mode and go to <b style='color:red;'>General Settings</b> and <b style='color:red;'>Document Template</b>" ), true);
                return $.Deferred().reject();
            }

            action = _.clone(action);

            var url = "/report/pdf/" + action.report_name;
            var title = action.name;
            var pdfFileName = action.name || action.display_name;
            var newUrl = false;
            // TS - bypass
            if(action.context.active_model === 'ins.financial.report' ||
                    action.context.active_model === 'ins.general.ledger' ||
                    action.context.active_model === 'ins.trial.balance' ||
                    action.context.active_model === 'ins.partner.ledger' ||
                    action.context.active_model === 'ins.partner.payment' ||
                    action.context.active_model === 'ins.partner.invoice' ||
                    action.context.active_model === 'ins.partner.ageing'){
                        return self._super(action, options);
                    }
            // end

            session.rpc(
                "/pdf_print_preview/get_report_name", 
                {
                    report_name: action.report_name, 
                    data: JSON.stringify(action.context)
                }).then(function(result) {

                pdfFileName = result['file_name'] || pdfFileName;

                if( pdfFileName !== undefined )
                    pdfFileName = "?" + pdfFileName.replace(/[/?%#&=]/g, "") + ".pdf";

                if (_.isUndefined(action.data) || _.isNull(action.data) || (_.isObject(action.data) && _.isEmpty(action.data))) {
                    url += "/" + action.context.active_ids.join(",");
                    newUrl = url + pdfFileName;
                }

                else {
                    var serializedOptionsPath = 'options=' + encodeURIComponent(JSON.stringify(action.data));
                    serializedOptionsPath += '&context=' + encodeURIComponent(JSON.stringify(action.context));
                    newUrl = url;
                    url += "?" + serializedOptionsPath;
                    newUrl += pdfFileName + "&" + serializedOptionsPath;
                }
                       

                if (action.report_type === "qweb-pdf" && session.preview_print) {
                    wkhtmltopdf_state = result['wkhtmltopdf_state'];
                    if (WKHTMLTOPDF_MESSAGES[wkhtmltopdf_state]) {
                        self.do_notify( _t("Report"), WKHTMLTOPDF_MESSAGES[wkhtmltopdf_state], true);
                        return $.Deferred().reject();
                    }
                    framework.blockUI();

                    var def = $.Deferred()

                    PreviewDialog.createPreviewDialog(self, newUrl,  title);

                    framework.unblockUI();

                }

                if (action.report_type === "qweb-pdf" && session.automatic_printing) {
                   
                    try {
                        var pdf = window.open(url);
                        pdf.print();
                    }
                    catch(err) {
                       self.do_notify( _t("Report"), _t( "Please allow <b style='color: red;'>pop up</b> in your browser to <b>preview report</> in another tab." ), true);
                    }
                    
                }

            });

                if ((!session.automatic_printing && !session.preview_print) || action.report_type != "qweb-pdf") {
                    return self._super(action, options);
                }
                return $.Deferred().reject();
            }
    });

});
