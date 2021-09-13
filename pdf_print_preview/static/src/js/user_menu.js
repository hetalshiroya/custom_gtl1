odoo.define("pdf_print_preview.report_menu", function (require) {
    "use strict";

    var UserMenu = require("web.UserMenu");
    var session = require("web.session");

    UserMenu.include({
        _onMenuPreview: function() {
            var self = this;
            this.trigger_up("clear_uncommitted_changes", {
                callback: function() {
                    self._rpc({
                        route: "/web/action/load", 
                        params: { action_id: "pdf_print_preview.action_short_preview_print" }}).done(function(result) {
                        result.res_id = session.uid;
                        self.do_action(result);
                    });
                },
            });
        },
    });

});
