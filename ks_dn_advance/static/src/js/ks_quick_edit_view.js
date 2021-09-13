odoo.define('ks_dashboard_tv_ninja.ks_quick_edit_view', function(require){

    var ksQuickEdit = require('ks_dashboard_ninja.quick_edit_view');

    ksQuickEdit.QuickEditView.include({

    ks_Update_item : function(){
            var self = this;
            var ksChanges = this.controller.renderer.state.data;

            if(ksChanges['name']) this.item['name']=ksChanges['name'];

            self.item['ks_font_color'] = ksChanges['ks_font_color'];
            self.item['ks_list_view_layout'] = ksChanges['ks_list_view_layout'];
            self.item['ks_icon_select'] = ksChanges['ks_icon_select'];
            self.item['ks_icon'] = ksChanges['ks_icon'];
            self.item['ks_background_color'] = ksChanges['ks_background_color'];
            self.item['ks_default_icon_color'] = ksChanges['ks_default_icon_color'];
            if(ksChanges['ks_layout']) self.item['ks_layout'] = ksChanges['ks_layout'];
            self.item['ks_record_count'] = ksChanges['ks_record_count'];

            if(ksChanges['ks_list_view_data']) self.item['ks_list_view_data'] = ksChanges['ks_list_view_data'];

            if(ksChanges['ks_chart_data']) self.item['ks_chart_data'] = ksChanges['ks_chart_data'];

            if(ksChanges['ks_kpi_data']) self.item['ks_kpi_data'] = ksChanges['ks_kpi_data'];

            if(ksChanges['ks_list_view_type']) self.item['ks_list_view_type'] = ksChanges['ks_list_view_type'];

            self.item['ks_chart_item_color'] = ksChanges['ks_chart_item_color'];

//            self.item['ks_kpi_data'] = ksChanges['ks_kpi_data'];
            self.ksUpdateItemView();

        },

    });
});