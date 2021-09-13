odoo.define('odoo_recently_viewed_records.widget', function (require) {
    "use strict";
    
    var core = require('web.core');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;

    
    var RecentRecord = Widget.extend({
        template: 'odoo_recently_viewed_records.RecentRecord',
        events: {
            // "click .open-recent-record": "_onRecordMenuClick",
            "click .o_mail_channel_preview": "_onRecordFilterClick",
        },
        is_open: function() {
            return this.$el.hasClass('open');
        },
        start: function() {
            this.$records_preview = this.$('.o_mail_systray_dropdown_items');
            this._updateRecordPreview();
            return this._super();
        },
        _getRecordData: function(){
            var self = this;
            return ajax.jsonRpc("/get/recently/view/records", 'call', {})
            .done(function(data) {
                self.records = data;
            });
        },
        _getActivityModelViewID: function(model) {
            return this._rpc({
                model: model,
                method: 'get_activity_view_id'
            });
        },
        _isOpen: function() {
            return this.$el.hasClass('open');
        },
        _updateRecordPreview: function() {
            var self = this;
            self._getRecordData().then(function (){
                self.$records_preview.html(QWeb.render('odoo_recently_viewed_records.RecentRecordPreview', {
                    records : self.records
                }));
            });
        },
        _onRecordFilterClick: function(event) {
            var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
            var context = {};
            this.do_action({
                type: 'ir.actions.act_window',
                name: data.model_name,
                res_model:  data.res_model,
                res_id:  data.res_id,
                views: [[false, 'form']],
                search_view_id: [false],
                context:context,
                target:'current'
            }, {
                clear_breadcrumbs: true
            });
        },
        _onRecordMenuClick: function(event) {
            event.preventDefault();
            if (!this.is_open()) {
                this._updateRecordPreview();
            }
        },
    });
    SystrayMenu.Items.push(RecentRecord); 
});