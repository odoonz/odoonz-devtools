# Copyright 2020 O4SB
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class TestEmailing(models.Model):

    _name = "test.emailing"
    _description = "Test Emailing"
    _rec_name = "subject"

    subject = fields.Char(required=True)
    body_html = fields.Html(string="Body", sanitize_style=True)
    email_from = fields.Char("From")
    email_to = fields.Char("To")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "test_emailing_ir_attachments_rel",
        "test_emailing_id",
        "attachment_id",
        string="Attachments",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Sent")],
        string="Status",
        required=True,
        copy=False,
        default="draft",
    )
    thread_id = fields.Integer()

    def generate_email(self):
        """send email internally to mail alias
        Issue: have to use body_alternative because encode body will cause
                 _message_parse_extract_payload to create fault attachment
                 in document
        """
        self.ensure_one()
        attachments = []
        for attachment in self.attachment_ids.sudo():
            if attachment["datas"] is not False:
                attachments += [
                    (
                        attachment["name"],
                        base64.b64decode(attachment["datas"]),
                        attachment["mimetype"],
                    )
                ]
        email = self.env["ir.mail_server"].build_email(
            email_from=self.email_from,
            email_to=[self.email_to],
            subject=self.subject,
            body=self.body_html,
            body_alternative=self.body_html,
            attachments=attachments if attachments else None,
            subtype="html",
            subtype_alternative="html",
        )
        encoded_email = email.as_string()
        try:
            thread = self.env["mail.thread"].message_process(None, encoded_email)
            if thread:
                self.thread_id = thread
                self.sudo().write({"state": "done"})
            return self.thread_id
        except ValueError as exc:
            raise ValidationError(_("No alias found.")) from exc
