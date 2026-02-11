# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Manufacturing integration fields
    manufacturing_order_ids = fields.Many2many('mrp.production', 
                                               string='Manufacturing Orders',
                                               compute='_compute_manufacturing_orders')
    manufacturing_order_count = fields.Integer(string='MO Count', 
                                               compute='_compute_manufacturing_orders')
    
    is_for_manufacturing = fields.Boolean(string='For Manufacturing', 
                                          compute='_compute_is_for_manufacturing', 
                                          store=True)
    
    @api.depends('order_line', 'order_line.move_dest_ids')
    def _compute_manufacturing_orders(self):
        for order in self:
            production_ids = order.order_line.mapped('move_dest_ids.raw_material_production_id')
            order.manufacturing_order_ids = production_ids
            order.manufacturing_order_count = len(production_ids)
    
    @api.depends('order_line', 'order_line.move_dest_ids')
    def _compute_is_for_manufacturing(self):
        for order in self:
            order.is_for_manufacturing = bool(order.manufacturing_order_ids)
    
    def action_view_manufacturing_orders(self):
        self.ensure_one()
        return {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.manufacturing_order_ids.ids)],
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Link to manufacturing
    manufacturing_order_id = fields.Many2one('mrp.production', 
                                             string='Manufacturing Order',
                                             compute='_compute_manufacturing_order')
    
    @api.depends('move_dest_ids')
    def _compute_manufacturing_order(self):
        for line in self:
            if line.move_dest_ids:
                line.manufacturing_order_id = line.move_dest_ids[0].raw_material_production_id
            else:
                line.manufacturing_order_id = False
