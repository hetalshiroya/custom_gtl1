odoo.define('goexcel_visit.geolocation', function (require) {
'use strict';
require('web.dom_ready');
var basic_field = require('web.basic_fields').FieldChar;
//var AbstractField = require('web.AbstractField');
var registry = require('web.field_registry');


    var GPSLocation = basic_field.extend({
         //gps_location: "3.0",

         //var gps_lon_lat;
        //supportedFieldTypes: ['char'],
        //init: function () {

        //trigger during the page loading
        init: function () {
            //var $gps_lon_lat = '3.1000';
            //this.gps_location = '3.3000';
             //var formatValue = this._formatValue(this.value);
            //this.$el.empty().text(gps_location);
            //this.$el.val(gps_location);

            this._super.apply(this, arguments);

         },

        //trigger in the edit mode
         _renderEdit: function () {
            this._super.apply(this, arguments);
            var gps_location = '3.1000';
//            var self = this;
//              if (navigator.geolocation) {
//                navigator.geolocation.getCurrentPosition(self._get_location.bind(self));
//            }
            /*if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        //self = this;
                        alert("Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude);
                        //gps_location = "Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude;
                    })
            }*/
            //this._getLocation(this);
            //var gps_location = this.gps_lon_lat;
            //var gps_location =
            //var gps_location = '3.1000';
            this.$el.val(gps_location);

         },

        //trigger after saved or in read only mode (first load the form)
        _renderReadonly: function () {
             this._super.apply(this, arguments);
             //var gps_location = this._getLocation();
             //var gps_location = '3.2000';
             //var formatValue = this._formatValue(this.value);
              //this.$el.empty().text(gps_location);
             //this.$el.val(gps_location);
             this.$el.html(this.value);
        },

        //save the changes
        commitChanges: function () {
            this._setValue(this.$el.val());
            return this.$el;
        },
//            if (navigator.geolocation) {
//                navigator.geolocation.getCurrentPosition(
//                    function(position) {
//                        //alert("Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude);
//                        var gps_location = "Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude;

                        //this.$el.val(gps_location)
                        //this._super.apply(this, arguments);

//                        var pos = {
//                          lat: position.coords.latitude,
//                          lng: position.coords.longitude
//                        };

//                      //console.log(position.coords.latitude, position.coords.longitude);
//                    //
//                    //return pos;
//                    //this.$el.text(pos);
//                });
//            };





//        showLocation: function(position){
//            //alert("Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude);
//            //this.$el.val("Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude);
//            this.$gps_lon_lat = "Lat: " + position.coords.latitude + "Lon: " + position.coords.longitude;
//        },

    });

    registry.add('gps_location', GPSLocation);

//    return {
//        GPSLocation: GPSLocation,
//    };
});