# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta


class MaterialRequirementWizard(models.TransientModel):
    _name = 'material.requirement.wizard'
    _description = 'Material Requirement Planning Wizard'

    date_from = fields.Date(string='From Date', required=True, 
                            default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=True,
                          default=lambda self: fields.Date.today() + timedelta(days=30))
    
    product_ids = fields.Many2many('product.product', string='Products',
                                   help='Leave empty to analyze all products')
    
    include_sales = fields.Boolean(string='Include Sales Orders', default=True)
    include_manufacturing = fields.Boolean(string='Include Manufacturing Orders', default=True)
    
    def action_generate_requirements(self):
        self.ensure_one()
        
        requirements = self.env['manufacturing.material.requirement']
        
        # Get manufacturing orders in date range
        if self.include_manufacturing:
            domain = [
                ('state', 'not in', ['done', 'cancel']),
                ('date_start', '>=', self.date_from),
                ('date_start', '<=', self.date_to),
            ]
            
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))
            
            productions = self.env['mrp.production'].search(domain)
            
            for production in productions:
                for move in production.move_raw_ids:
                    if move.state not in ['done', 'cancel']:
                        requirements |= self.env['manufacturing.material.requirement'].create({
                            'product_id': move.product_id.id,
                            'required_quantity': move.product_uom_qty,
                            'required_date': production.date_start.date(),
                            'production_id': production.id,
                            'state': 'confirmed',
                        })
        
        # Get sales orders in date range
        if self.include_sales:
            domain = [
                ('state', 'in', ['sale', 'done']),
                ('commitment_date', '>=', self.date_from),
                ('commitment_date', '<=', self.date_to),
            ]
            
            sales = self.env['sale.order'].search(domain)
            
            for sale in sales:
                for line in sale.order_line:
                    if self.product_ids and line.product_id not in self.product_ids:
                        continue
                    
                    # Check if product has BoM
                    if line.product_id.bom_ids:
                        bom = line.product_id.bom_ids[0]
                        for bom_line in bom.bom_line_ids:
                            requirements |= self.env['manufacturing.material.requirement'].create({
                                'product_id': bom_line.product_id.id,
                                'required_quantity': bom_line.product_qty * line.product_uom_qty,
                                'required_date': sale.commitment_date,
                                'sale_order_id': sale.id,
                                'state': 'draft',
                            })
        
        return {
            'name': _('Material Requirements'),
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.material.requirement',
            'view_mode': 'list,form',
            'domain': [('id', 'in', requirements.ids)],
            'target': 'current',
        }
