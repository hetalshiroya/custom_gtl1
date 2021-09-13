odoo.define('aspl_web_tinymce_editor.web_tinymce', function(require) {
    "use strict";

    var editor_backend = require('web_editor.backend');
    var config = require('web.config');
    var is_tinymce = false;
    var transcoder = require('web_editor.transcoder');

    var FieldTextHtmlSimple = editor_backend.FieldTextHtmlSimple.include({

        _renderEdit: function() {
            var self = this
            this.$textarea = $('<textarea>');
            this.$textarea.appendTo(this.$el);
            this._rpc({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['aspl_web_tinymce_editor.is_tinymce'],
                }, {
                    async: false
                })
                .then(function(res) {
                    if (res) {
                        is_tinymce = true
                    }
                })
            if (is_tinymce) {
                this.$el.find('textarea').attr("class", self.name);
                this.$el.find('textarea').attr("data-text-id", self.name);
                this.$textarea.val(self._textToHtml(self.value));
                this.$content = this.$el.find('textarea');
                this.$content.html(self._textToHtml(self.value));
                tinymce.remove();
                setTimeout(function() {
                    var $tinymce_ed = tinymce.init({
                        selector: '.oe_form_field_html_text textarea',
                        custom_ui_selector: '.' + self.name,
                        height: 300,
                        width: 'auto',
                        resize: false,
                        theme: 'modern',
                        plugins: [
                            'advlist autolink link image imagetools lists colorpicker insertdatetime charmap print fullpage fullscreen preview hr media table emoticons imagetools code nonbreaking pagebreak searchreplace tabfocus textcolor textpattern wordcount autosave save'
                        ],
                        autosave_interval: "5s",
                        image_advtab: true,
                        theme_advanced_buttons3_add: "save",
                        autosave_ask_before_unload: false,
                        save_enablewhendirty: true,
                        save_onsavecallback: function() {
                            $(document).find('.o_form_button_save').trigger('click')
                            alert("Record Saved")
                            $(document).find('.o_form_button_edit').trigger('click')
                        },
                        toolbar: 'undo redo save | formatselect | sizeselect |  fontselect |  fontsizeselect | bold italic underline forecolor backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | insertdatetime image media link table hr nonbreaking pagebreak | removeformat | fullscreen',
                    });
					var history = this.$textarea;
                if (history) {
                    history.reset();
                }
                }, 200);
            } else {
                this.$textarea.summernote(this._getSummernoteConfig());
                this.$content = this.$('.note-editable:first');
                this.$content.html(this._textToHtml(this.value));
                // trigger a mouseup to refresh the editor toolbar
                var mouseupEvent = $.Event('mouseup', {
                    'setStyleInfoFromEditable': true
                });
                this.$content.trigger(mouseupEvent);
                if (this.nodeOptions['style-inline']) {
                    transcoder.styleToClass(this.$content);
                    transcoder.imgToFont(this.$content);
                    transcoder.linkImgToAttachmentThumbnail(this.$content);
                }
                // reset the history (otherwise clicking on undo before editing the
                // value will empty the editor)
                var history = this.$content.data('NoteHistory');
                if (history) {
                    history.reset();
                }
            }
            this.$('.note-toolbar').append(this._renderTranslateButton());
        },

		reset: function (record, event) {
			this._reset(record, event);
			var self = this
			if (!event || event.target !== this) {
				if (this.mode === 'edit') {
					if (is_tinymce) {
                        for (var inst in tinyMCE.editors) {
                            if (tinyMCE.editors[inst].getContent) {
                                var id = '#' + tinyMCE.editors[inst].id
                                if ($(id).data('text-id') == this.name) {
                                    tinyMCE.activeEditor.setContent(this.value);
                                }
                            }
                        }
					}
					else{
						this.$content.html(this._textToHtml(this.value));
					}
				} else {
					this._renderReadonly();
				}
			}
			return $.when();
		},

        _getValue: function() {
            if (is_tinymce) {
                for (var inst in tinyMCE.editors) {
                    if (tinyMCE.editors[inst].getContent) {
                        var id = '#' + tinyMCE.editors[inst].id
                        if ($(id).data('text-id') == this.name) {
                            return tinyMCE.editors[inst].getContent()
                        }
                    }
                }
            } else {
                if (this.nodeOptions['style-inline']) {
                    transcoder.attachmentThumbnailToLinkImg(this.$content);
                    transcoder.fontToImg(this.$content);
                    transcoder.classToStyle(this.$content);
                }
                return this.$content.html();
            }
        },
    });
});