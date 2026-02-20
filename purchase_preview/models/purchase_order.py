from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    manager_id = fields.Many2one('res.users', string="Manager")
    is_manager_confirmed = fields.Boolean(string="Manager Confirmed?", default=False, copy=False)

    def action_preview_purchase_order(self):
        self.ensure_one()
        return {
            'name': 'Generate Preview Link',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }
