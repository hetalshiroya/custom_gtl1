odoo.define("pdf_print_preview.PreviewDialog", function (require) {
"use strict";

var core = require("web.core");
var framework = require("web.framework");
var Widget = require("web.Widget");

var QWeb = core.qweb;
var _t = core._t;

var pdfPreview = core.Class.extend({

    preview: function( url ) {
        var result = $.Deferred();  
        var urlTempalte = _.template("/pdf_print_preview/static/lib/PDFjs/web/viewer.html?file=<%= url %>");
        result.resolve($(QWeb.render("PDFjsFrame", {url: urlTempalte({url})})));

        return $.when(result);        
    }

});

var PreviewDialog = Widget.extend({
	init: function(parent, pdfPreview, url, title) {
		this._super(parent);
        this._opened = $.Deferred();
        this.title = title || _t("Preview");
        this.url = url;
		this.$modal = $(QWeb.render("PreviewDialog", {title: this.title, url: this.url}));
        this.$modal.on("hidden.bs.modal", _.bind(this.destroy, this));
        this.$modal.find(".preview-maximize").on("click", _.bind(this.maximize, this));
        this.$modal.find(".preview-minimize").on("click", _.bind(this.minimize, this));
        this.$modal.find(".preview-maximize").toggle();
		this.pdfPreview = pdfPreview;
	},
    renderElement: function() {
        this._super();
        var self = this;

        this.pdfPreview.preview(this.url).then(function($content) {
            self.setElement($("<div/>").addClass("modal-body preview-body").append($content));
        });
	},
    open: function() {
        var self = this;
        $(".tooltip").remove();
        this.replace(this.$modal.find(".modal-body")).then(function() {
            self.$modal.modal("show");
            self._opened.resolve();
        });
        return self;
    },
    maximize: function(e) {
    	this.$modal.find(".preview-maximize").toggle();
    	this.$modal.find(".preview-minimize").toggle();
        this.$modal.find(".modal-dialog").addClass("modal-full");
    	
    },
    minimize: function(e) {
    	this.$modal.find(".preview-maximize").toggle();
    	this.$modal.find(".preview-minimize").toggle();
        this.$modal.find(".modal-dialog").removeClass("modal-full");
    },
    close: function() {
        this.$modal.modal("hide");
    },
    destroy: function(reason) {
        $(".tooltip").remove();
        if(this.isDestroyed()) {
            return;
        }
        this.trigger("closed", reason);
        this._super();
        this.$modal.modal("hide");
        this.$modal.remove();
        setTimeout(function () {
            var modals = $("body > .modal").filter(":visible");
            if(modals.length) {
                modals.last().focus();
                $("body").addClass("modal-open");
            }
        }, 0);
    }
});

PreviewDialog.createPreviewDialog = function (parent, url, title) {
    return new PreviewDialog(parent, new pdfPreview(), url, title).open();
};

return PreviewDialog;

});