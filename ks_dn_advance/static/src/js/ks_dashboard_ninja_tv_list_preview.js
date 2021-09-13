odoo.define('ks_dashboard_tv_ninja.ks_list_view_preview', function(require){

    var KsListPreview = require('ks_dashboard_ninja_list.ks_dashboard_ninja_list_view_preview');
    var viewRegistry = require('web.view_registry');
    var field_utils = require('web.field_utils');
    var core = require('web.core');
    var QWeb = core.qweb;

    KsListPreview.KsListViewPreview.include({

        _render: function(){
            this.$el.empty();
            var rec =  this.recordData;
            if (rec.ks_dashboard_item_type === 'ks_list_view') {
                if(rec.ks_data_calculation_type === "custom"){
                    this._super.apply(this, arguments);
                } else {
                    this.ksRenderListView();
                }
            }
        },

        ksRenderListView: function() {
            var field = this.recordData;
            var ks_list_view_name;
            var list_view_data = JSON.parse(field.ks_list_view_data);
            var count = field.ks_record_count;
            if (field.name) ks_list_view_name = field.name;
            else if (field.ks_model_name) ks_list_view_name = field.ks_model_id.data.display_name;
            else ks_list_view_name = "Name";
            if (field.ks_list_view_type === "ungrouped" && list_view_data) {
                var index_data = list_view_data.date_index;
                for (var i = 0; i < index_data.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows.length; j++) {
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]
                        if (date){
                             if( list_view_data.fields_type[i] === 'date'){
                                    list_view_data.data_rows[j]["data"][index] = field_utils.format.date(moment(moment(date).utc(true)._d), {}, {
                                timezone: false
                            });}else{
                                list_view_data.data_rows[j]["data"][index] = field_utils.format.datetime(moment(moment(date).utc(true)._d), {}, {
                                timezone: false
                            });
                            }

                        }else {
                            list_view_data.data_rows[j]["data"][index] = "";
                        }
                    }
                }
            }

            if (field.ks_list_view_data) {
                var data_rows = list_view_data.data_rows;
                for (var i = 0; i < list_view_data.data_rows.length; i++) {
                    for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++) {
                        if (typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]) {
                            if (typeof(list_view_data.data_rows[i].data[j]) === "number") {
                                list_view_data.data_rows[i].data[j] = field_utils.format.float(list_view_data.data_rows[i].data[j], Float64Array)
                            }
                        } else {
                            list_view_data.data_rows[i].data[j] = "";
                        }
                    }
                }
            } else list_view_data = false;
            count = list_view_data && field.ks_list_view_type === "ungrouped" ? count - list_view_data.data_rows.length : false;
            count = count ? count <=0 ? false : count : false;
            var $listViewContainer = $(QWeb.render('ks_list_view_container', {
                ks_list_view_name: ks_list_view_name,
                list_view_data: list_view_data,
                count: count,
                layout: field.ks_list_view_layout,
            }));
            if (!this.recordData.ks_show_records === true) {
                $listViewContainer.find('#ks_item_info').hide();
            }
            if (count && field.ks_data_calculation_type === 'custom'){
                $listViewContainer.find('tbody').append($(QWeb.render('ks_record_more',{
                    count,count,
                })));
            }

            this.$el.append($listViewContainer);
        },

        get_rgba_format: function(val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function(v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        },
    });

    return KsListPreview;
});