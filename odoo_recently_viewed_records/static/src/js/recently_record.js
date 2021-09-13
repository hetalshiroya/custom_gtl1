odoo.define('odoo_recently_viewed_records.get_view_url', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var QWeb = core.qweb;

    FormRenderer.include({
        _updateView: function(e) {
            var self = this;
            this._super.apply(this, arguments);
            var url = this.$el.context.baseURI;
            var components = URI.parse(url);
            var query = URI.parseQuery(components['fragment']);
            var vals = {
                'name': this.state.data.display_name,
                'url': this.$el.context.baseURI,
                'action': parseInt(query['action']) || false,
                'record_id': this.state.data.id,
                'model': this.state.model,
            }
            ajax.jsonRpc("/recently/view/records", 'call', vals)
            .then(function(data) {
                if (data['status']) {
                    self._updateRecordPreview(data.records_list);
                }
            });
        },
        _updateRecordPreview: function(records) {
            var self = this;
            $('.o_mail_systray_dropdown_items').html(
                QWeb.render('odoo_recently_viewed_records.RecentRecordPreview', {
                    records : records
                })
            );
        },
    });
});
