# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Manufacturing integration fields
    manufacturing_order_ids = fields.Many2many('mrp.production', 
                                               string='Manufacturing Orders',
                                               compute='_compute_manufacturing_orders')
    manufacturing_order_count = fields.Integer(string='MO Count', 
                                               compute='_compute_manufacturing_orders')
    
    require_manufacturing = fields.Boolean(string='Require Manufacturing', 
                                           compute='_compute_require_manufacturing', 
                                           store=True)
    
    manufacturing_state = fields.Selection([
        ('none', 'No Manufacturing'),
        ('to_produce', 'To Produce'),
        ('in_production', 'In Production'),
        ('produced', 'Produced'),
    ], string='Manufacturing Status', compute='_compute_manufacturing_state', 
       store=True)
    
    @api.depends('order_line', 'order_line.move_ids')
    def _compute_manufacturing_orders(self):
        for order in self:
            productions = self.env['mrp.production'].search([
                ('origin', '=', order.name)
            ])
            order.manufacturing_order_ids = productions
            order.manufacturing_order_count = len(productions)
    
    @api.depends('order_line', 'order_line.product_id')
    def _compute_require_manufacturing(self):
        for order in self:
            order.require_manufacturing = any(
                line.product_id.bom_ids for line in order.order_line
            )
    
    @api.depends('manufacturing_order_ids', 'manufacturing_order_ids.state')
    def _compute_manufacturing_state(self):
        for order in self:
            if not order.manufacturing_order_ids:
                order.manufacturing_state = 'none'
            elif all(mo.state in ['done', 'cancel'] for mo in order.manufacturing_order_ids):
                order.manufacturing_state = 'produced'
            elif any(mo.state in ['progress', 'to_close'] for mo in order.manufacturing_order_ids):
                order.manufacturing_state = 'in_production'
            else:
                order.manufacturing_state = 'to_produce'
    
    def action_view_manufacturing_orders(self):
        self.ensure_one()
        return {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.manufacturing_order_ids.ids)],
            'context': {'create': False},
        }
    
    def action_create_manufacturing_orders(self):
        """Create manufacturing orders for products with BoM"""
        self.ensure_one()
        created_orders = self.env['mrp.production']
        
        for line in self.order_line.filtered(lambda l: l.product_id.bom_ids):
            # Get the appropriate BoM for the product
            bom_dict = self.env['mrp.bom']._bom_find(
                line.product_id,
                company_id=self.company_id.id,
                bom_type='normal'
            )
            
            # _bom_find returns a defaultdict, index by product to get the BoM
            bom = bom_dict.get(line.product_id)
            
            if bom:
                mo = self.env['mrp.production'].create({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'product_uom_id': line.product_uom.id,
                    'bom_id': bom.id,
                    'origin': self.name,
                    'date_start': fields.Datetime.now(),
                })
                created_orders |= mo
        
        if created_orders:
            return {
                'name': _('Manufacturing Orders'),
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_orders.ids)],
            }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Manufacturing fields
    manufacturing_order_id = fields.Many2one('mrp.production', 
                                             string='Manufacturing Order',
                                             compute='_compute_manufacturing_order')
    has_bom = fields.Boolean(string='Has BoM', compute='_compute_has_bom')
    
    @api.depends('move_ids')
    def _compute_manufacturing_order(self):
        for line in self:
            production = self.env['mrp.production'].search([
                ('origin', '=', line.order_id.name),
                ('product_id', '=', line.product_id.id),
            ], limit=1)
            line.manufacturing_order_id = production
    
    @api.depends('product_id')
    def _compute_has_bom(self):
        for line in self:
            line.has_bom = bool(line.product_id.bom_ids)
