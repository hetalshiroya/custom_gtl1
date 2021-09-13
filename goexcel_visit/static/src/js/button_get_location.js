odoo.define('goexcel_visit.button_geolocation', function (require) {
'use strict';

var FormController = require('web.FormController');
    var formController = FormController.include({
        _onButtonClicked: function (event) {
            if(event.data.attrs.id === "get_location_check_in"){
                event.stopPropagation();
                var attrs = event.data.attrs;
                var record = event.data.record;
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            var rpc = require('web.rpc');
                            var gps_location = position.coords.latitude + "," + position.coords.longitude;
                            var record_id =  record.res_id;
                            rpc.query({
                                model: 'visit',
                                method: 'update_check_in_location',
                                args: [gps_location, record_id],
                            }).always(function () {
                                //self.destroy();
                            });
                        }
                    )
                }
            }
            if(event.data.attrs.id === "get_location_check_out"){
                event.stopPropagation();
                var attrs = event.data.attrs;
                var record = event.data.record;
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            var rpc = require('web.rpc');
                            var gps_location = position.coords.latitude + "," + position.coords.longitude;
                            //alert('current id:' + record.res_id);
                            var record_id =  record.res_id;
                            rpc.query({
                                model: 'visit',
                                method: 'update_check_out_location',
                                args: [gps_location, record_id],
                            }).always(function () {
                                //self.destroy();
                            });
                        }
                    )
                }
            }
            if(event.data.attrs.id === "get_location"){
                event.stopPropagation();
                var attrs = event.data.attrs;
                var record = event.data.record;
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            var rpc = require('web.rpc');
                            var gps_location = position.coords.latitude + "," + position.coords.longitude;
                            var record_id =  record.res_id;
                            var destination = record.data.destination;
                            var url = 'https://www.google.com/maps/dir/' + gps_location + '/' + destination
                            window.open(url);
                        }
                    )
                }
            }
            this._super(event);
        },
    });
});
