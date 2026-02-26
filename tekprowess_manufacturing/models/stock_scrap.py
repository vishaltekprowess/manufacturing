# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    reverse_move_ids = fields.Many2many('stock.move', 'stock_scrap_reverse_move_rel', 'scrap_id', 'move_id', string="Reverse Moves", readonly=True)
    reverted_qty = fields.Float('Reverted Quantity', copy=False, default=0.0, readonly=True)

    def action_get_stock_move_lines(self):
        action = super().action_get_stock_move_lines()
        all_move_ids = self.move_ids.ids + self.reverse_move_ids.ids
        if 'domain' in action:
            action['domain'] = [('move_id', 'in', all_move_ids)]
        return action

    def action_open_reverse_wizard(self):
        self.ensure_one()
        return {
            'name': _('Reverse Scrap'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.scrap.reverse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scrap_id': self.id}
        }
