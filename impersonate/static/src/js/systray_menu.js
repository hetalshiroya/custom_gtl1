odoo.define('impersonate.SystrayMenu', function(require) {
	"use strict";

	var session = require('web.session');
	var ajax = require('web.ajax');
	var SystrayMenu = require('web.SystrayMenu');
	var Widget = require('web.Widget');

	var ImpersonateSystrayMenu = Widget.extend({
		template : 'Impersonate.SystrayMenu',
		events : {
			'click' : '_onClick',
		},

		_onClick : function(ev) {
			ev.preventDefault();
			var self = this;
			this.trigger_up('clear_uncommitted_changes', {
				callback : function() {
					ajax.rpc('/impersonate/exit', {}).then(function(result) {
						self.do_action(result);
					});
				},
			});
		},
	});

	if (session.impersonator_uid) {
		SystrayMenu.Items.push(ImpersonateSystrayMenu);
	}

	return ImpersonateSystrayMenu;

});