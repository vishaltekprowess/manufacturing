from odoo import models, fields, api

class PurchasePreviewWizard(models.TransientModel):
    _name = 'purchase.preview.wizard'
    _description = 'Purchase Order Preview Wizard'

    order_id = fields.Many2one('purchase.order', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Select User/Partner", required=True)
    preview_link = fields.Char(string="Preview Link", compute="_compute_preview_link")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'order_id' in res:
            order = self.env['purchase.order'].browse(res['order_id'])
            if order.manager_id:
                res['partner_id'] = order.manager_id.partner_id.id
        return res

    @api.depends('partner_id', 'order_id')
    def _compute_preview_link(self):
        for wizard in self:
            if wizard.order_id and wizard.partner_id:
                base_url = wizard.env['ir.config_parameter'].sudo().get_param('web.base.url')
                share_url = wizard.order_id._get_share_url(pid=wizard.partner_id.id)
                wizard.preview_link = f"{base_url}{share_url}"
            else:
                wizard.preview_link = False
