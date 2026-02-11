# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpProductionWizard(models.TransientModel):
    _name = 'mrp.production.wizard'
    _description = 'Manufacturing Order Creation Wizard'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', 
                                     compute='_compute_product_uom_id')
    bom_id = fields.Many2one('mrp.bom', string='Bill of Materials', 
                             domain="[('product_id', '=', product_id)]")
    
    production_type = fields.Selection([
        ('standard', 'Standard Production'),
        ('make_to_order', 'Make to Order'),
        ('subcontracting', 'Subcontracting'),
        ('rework', 'Rework'),
    ], string='Production Type', default='standard', required=True)
    
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='0')
    
    date_start = fields.Datetime(string='Planned Start Date', 
                                 default=fields.Datetime.now)
    
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    
    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for wizard in self:
            wizard.product_uom_id = wizard.product_id.uom_id
    
    def action_create_production(self):
        self.ensure_one()
        
        if not self.bom_id:
            # Try to find default BoM
            bom = self.env['mrp.bom']._bom_find(
                product=self.product_id,
                company_id=self.env.company.id,
            )[self.product_id]
            
            if not bom:
                raise UserError(_('No Bill of Materials found for product %s') % self.product_id.name)
        else:
            bom = self.bom_id
        
        production = self.env['mrp.production'].create({
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'bom_id': bom.id,
            'production_type': self.production_type,
            'priority': self.priority,
            'date_start': self.date_start,
            'origin': self.sale_order_id.name if self.sale_order_id else False,
        })
        
        return {
            'name': _('Manufacturing Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
            'target': 'current',
        }
