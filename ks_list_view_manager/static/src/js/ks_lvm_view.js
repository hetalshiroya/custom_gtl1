odoo.define('ks_list_view_manager.ks_lvm_view', function (require) {
    "use strict";

    var ListView = require('web.ListView');
    var rpc = require('web.rpc');
    var utils = require('web.utils');

    ListView.include({

        getRenderer: function () {
            var self = this;
                self.rendererParams.arch = _.extend({},self.arch);
                self.rendererParams = _.extend({},{'ks_lvm_data':self.fieldsView.ks_lvm_user_data || false},self.rendererParams);
                return self._super.apply(this,arguments);
        },

        getController: function () {
            var self = this;
            var parent_super = self._super;
            var ks_arguments = arguments;
            var ks_fetch_options = {
                'ks_model': self.fieldsView.model,
                'ks_view_id': self.fieldsView.ks_lvm_user_data.ksViewID || false,
            }

             return rpc.query({
                route: '/ks_lvm_control/ks_generate_arch_view',
                params: {
                    'ks_model': self.fieldsView.model,
                    'ks_view_id': self.fieldsView.ks_lvm_user_data.ksViewID || false,
                }
            },{async: false}).then(function(ks_list_view_data){

                // parsing arch and node
                var doc = $.parseXML(ks_list_view_data.fields_views["list"].arch).documentElement;
                self.arch = _.extend({},utils.xml_to_json(doc, true));
                var node;
                for(var i =0;i < self.arch.children.length;i++) {
                    node = self.arch.children[i];
                    if (!_.isObject(node.attrs.modifiers)) {
                        node.attrs.modifiers = node.attrs.modifiers ? JSON.parse(node.attrs.modifiers) : {};
                    }
                    self.arch.children[i] = node;
                }

                //  setting editable mode
                if(self.arch.attrs.editable){
                    self.controllerParams.editable = self.arch.attrs.editable;
                    self.controllerParams.mode = "edit";
                    self.rendererParams.editable =  self.arch.attrs.editable;
                } else {
                    self.controllerParams.editable = false;
                    self.controllerParams.mode = "readonly";
                    self.rendererParams.editable =  false;
                }

                ks_list_view_data.fields_views["list"]["ks_lvm_user_data"]['default_fields'] = ks_list_view_data["fields"];
                self.fieldsView.ks_lvm_user_data = _.extend({},ks_list_view_data.fields_views["list"]["ks_lvm_user_data"]);
                self.controllerParams = _.extend({},{'ks_lvm_data':self.fieldsView.ks_lvm_user_data || false},self.controllerParams);
                return parent_super.apply(self,ks_arguments);
            });
        },

    });

});


