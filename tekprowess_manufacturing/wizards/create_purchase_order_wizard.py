# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CreatePurchaseOrderWizard(models.TransientModel):
    _name = 'create.purchase.order.wizard'
    _description = 'Create Purchase Order from Manufacturing Order'

    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True)
    line_ids = fields.One2many('create.purchase.order.wizard.line', 'wizard_id', string='Materials to Purchase')
    company_id = fields.Many2one('res.company', related='production_id.company_id', store=True)
    
    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard with materials that need to be purchased"""
        res = super().default_get(fields_list)
        production_id = self.env.context.get('active_id')
        
        if production_id:
            production = self.env['mrp.production'].browse(production_id)
            res['production_id'] = production_id
            
            # Analyze material requirements
            lines = []
            for move in production.move_raw_ids:
                product = move.product_id
                
                # Skip if product is not purchasable
                if not product.purchase_ok:
                    continue
                
                # Get available quantity
                available_qty = product.with_context(
                    location=production.location_src_id.id
                ).qty_available
                
                required_qty = move.product_uom_qty
                shortage = max(0, required_qty - available_qty)
                
                # Only add if there's a shortage
                if shortage > 0:
                    # Get preferred supplier
                    supplier = product.seller_ids[:1] if product.seller_ids else None
                    
                    lines.append((0, 0, {
                        'product_id': product.id,
                        'required_qty': required_qty,
                        'available_qty': available_qty,
                        'shortage_qty': shortage,
                        'purchase_qty': shortage,
                        'product_uom_id': move.product_uom.id,
                        'supplier_id': supplier.partner_id.id if supplier else False,
                        'unit_price': supplier.price if supplier else product.standard_price,
                        'selected': True,
                    }))
            
            res['line_ids'] = lines
        
        return res
    
    def action_create_purchase_order(self):
        """Create purchase order(s) from selected lines"""
        self.ensure_one()
        
        selected_lines = self.line_ids.filtered(lambda l: l.selected and l.purchase_qty > 0)
        
        if not selected_lines:
            raise UserError(_('Please select at least one material to purchase.'))
        
        # Group lines by supplier
        po_by_supplier = {}
        for line in selected_lines:
            if not line.supplier_id:
                raise UserError(_('Please select a supplier for %s') % line.product_id.display_name)
            
            if line.supplier_id not in po_by_supplier:
                po_by_supplier[line.supplier_id] = []
            po_by_supplier[line.supplier_id].append(line)
        
        # Create purchase orders
        created_pos = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        
        for supplier, lines in po_by_supplier.items():
            # Create PO first
            po = self.env['purchase.order'].create({
                'partner_id': supplier.id,
                'origin': self.production_id.name,
                'date_order': fields.Datetime.now(),
                'company_id': self.company_id.id,
            })
            
            # Add order lines
            for line in lines:
                product = line.product_id
                
                # Get product description (purchase description or default name)
                product_lang = product.with_context(
                    lang=supplier.lang,
                    partner_id=supplier.id,
                )
                name = product_lang.display_name
                if product_lang.description_purchase:
                    name += '\n' + product_lang.description_purchase
                
                # Create purchase order line
                po_line = PurchaseOrderLine.create({
                    'order_id': po.id,
                    'product_id': product.id,
                    'name': name,
                    'product_qty': line.purchase_qty,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.unit_price,
                    'date_planned': self.production_id.date_start or fields.Datetime.now(),
                })
                
                # Link PO line to corresponding stock move
                # Find the stock move for this product in the MO
                stock_move = self.production_id.move_raw_ids.filtered(
                    lambda m: m.product_id == product
                )
                if stock_move:
                    # Link the PO line to the stock move
                    stock_move[:1].write({
                        'created_purchase_line_ids': [(4, po_line.id)]
                    })
            
            created_pos |= po
        
        # Recompute purchase order count on MO to update stat button
        self.production_id._compute_purchase_orders()
        
        # Show created purchase orders
        if len(created_pos) == 1:
            return {
                'name': _('Purchase Order'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'res_id': created_pos.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'name': _('Purchase Orders'),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_pos.ids)],
                'target': 'current',
            }


class CreatePurchaseOrderWizardLine(models.TransientModel):
    _name = 'create.purchase.order.wizard.line'
    _description = 'Purchase Order Wizard Line'

    wizard_id = fields.Many2one('create.purchase.order.wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    required_qty = fields.Float(string='Required', digits='Product Unit of Measure')
    available_qty = fields.Float(string='Available', digits='Product Unit of Measure')
    shortage_qty = fields.Float(string='Shortage', digits='Product Unit of Measure')
    purchase_qty = fields.Float(string='Quantity to Purchase', digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    supplier_id = fields.Many2one('res.partner', string='Supplier', domain="[('supplier_rank', '>', 0)]")
    unit_price = fields.Float(string='Unit Price', digits='Product Price')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', digits='Product Price')
    selected = fields.Boolean(string='Select', default=True)
    
    @api.depends('purchase_qty', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.purchase_qty * line.unit_price
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update supplier and price when product changes"""
        if self.product_id:
            supplier = self.product_id.seller_ids[:1]
            if supplier:
                self.supplier_id = supplier.partner_id
                self.unit_price = supplier.price
            else:
                self.unit_price = self.product_id.standard_price
