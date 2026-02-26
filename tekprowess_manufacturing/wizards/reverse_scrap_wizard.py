# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockScrapReverseWizard(models.TransientModel):
    _name = 'stock.scrap.reverse.wizard'
    _description = 'Reverse Scrap Wizard'

    scrap_id = fields.Many2one('stock.scrap', string='Scrap Record', required=True, readonly=True)
    revert_qty = fields.Float('Reverse Quantity', required=True, digits='Product Unit of Measure')
    company_id = fields.Many2one('res.company', related='scrap_id.company_id')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_id') and self._context.get('active_model') == 'stock.scrap':
            res['scrap_id'] = self._context.get('active_id')
        return res

    def action_reverse_scrap(self):
        self.ensure_one()
        if self.revert_qty <= 0:
            raise UserError(_("Reverse quantity must be greater than zero."))
        
        # Ensure we don't revert more than available
        available_to_revert = self.scrap_id.scrap_qty - self.scrap_id.reverted_qty
        if self.revert_qty > available_to_revert:
            raise UserError(_("Cannot reverse more than the remaining scrapped quantity (%s).") % available_to_revert)

        scrap = self.scrap_id

        # 1. Create a reverse stock move
        # Mirror Odoo 18 standard _prepare_move_values by explicitly declaring move_line_ids
        # to ensure serials/lots/packages are properly tracked back.
        move_vals = {
            'name': _('Reverse Scrap: %s') % scrap.name,
            'origin': scrap.origin or scrap.picking_id.name or scrap.name,
            'company_id': scrap.company_id.id,
            'product_id': scrap.product_id.id,
            'product_uom': scrap.product_uom_id.id,
            'state': 'draft',
            'product_uom_qty': self.revert_qty,
            # Reverse locations! Moving from Scrap Location back to Source Location
            'location_id': scrap.scrap_location_id.id,
            'location_dest_id': scrap.location_id.id,
            'scrapped': False, # It is moving BACK to stock
            'scrap_id': scrap.id,
            'picking_id': scrap.picking_id.id if hasattr(scrap, 'picking_id') else False,
            'move_line_ids': [(0, 0, {
                'product_id': scrap.product_id.id,
                'product_uom_id': scrap.product_uom_id.id,
                'quantity': self.revert_qty,
                'location_id': scrap.scrap_location_id.id,
                'location_dest_id': scrap.location_id.id,
                'package_id': scrap.package_id.id,
                'owner_id': scrap.owner_id.id,
                'lot_id': scrap.lot_id.id,
            })],
            'picked': True,
        }

        move = self.env['stock.move'].create(move_vals)
        move.with_context(is_scrap=True)._action_done()

        # 2. Add to reverted quantity and link reverse move
        scrap.write({
            'reverted_qty': scrap.reverted_qty + self.revert_qty,
            'reverse_move_ids': [(4, move.id)]
        })

        return {'type': 'ir.actions.act_window_close'}
