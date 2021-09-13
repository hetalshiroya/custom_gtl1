odoo.define('sci_goexcel_freight.si_website_popup_add', function (require) {
'use strict';

//var Model = require('web.Model');
//var base = require('web_editor.base');
//var options = require('web_editor.snippets.options');
//var session = require('web.session');
//var website = require('website.website');
var core = require('web.core');
var website = require('website.website');

    $(document).ready(function () {
        $('#popup_add_line_button').click(function(){
            $('#oe_generic_popup_modal').modal('show');
           //alert(core._t('Hello world'));
        })
        $('#popup_edit_line_button').click(function(){
            $('#oe_edit_line_popup_modal').modal('show');
           //alert(core._t('Hello world'));
        })

    })

   /* $("#popup_button").on('click', function () {
        //$('#oe_generic_popup_modal').modal('show');
        alert(core._t('Hello world'));
    });*/

});