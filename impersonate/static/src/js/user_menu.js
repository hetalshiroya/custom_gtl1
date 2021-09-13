odoo.define('impersonate.UserMenu', function(require) {
	"use strict";
	var UserMenu = require('web.UserMenu');
	var session = require('web.session');
	var ajax = require('web.ajax');

	UserMenu.include({
		start : function() {
			if (!session.impersonator_uid) {
				this.$el.find('a[data-menu="impersonate_stop"]').remove();
			}
			if (session.impersonator_uid || !session.impersonate_check) {
				this.$el.find('a[data-menu="impersonate"]').remove();
			}

			return this._super.apply(this, arguments);
		},

		_onMenuImpersonate : function() {
			var self = this;
			this.trigger_up('clear_uncommitted_changes', {
				callback : function() {
					ajax.rpc('/web/action/load', {
						action_id : 'impersonate.action_impersonate'
					}).then(function(result) {
						self.do_action(result);
					});
				},
			});
		},

		_onMenuImpersonate_stop : function() {
			var self = this;
			this.trigger_up('clear_uncommitted_changes', {
				callback : function() {
					ajax.rpc('/impersonate/exit', {}).then(function(result) {
						self.do_action(result);
					});
				},
			});
		}

	});

});