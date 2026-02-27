# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class TekprowessManufacturingDashboard(models.TransientModel):
    _name = 'tekprowess.manufacturing.dashboard'
    _description = 'Tekprowess Manufacturing Dashboard'

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_month_labels(self, n=6):
        today = date.today()
        months = []
        for i in range(n - 1, -1, -1):
            d = today - relativedelta(months=i)
            start = d.replace(day=1)
            end = (start + relativedelta(months=1)) - timedelta(days=1)
            months.append({
                'label': start.strftime('%b'),
                'start': fields.Datetime.to_datetime(str(start) + ' 00:00:00'),
                'end': fields.Datetime.to_datetime(str(end) + ' 23:59:59'),
            })
        return months

    # -------------------------------------------------------------------------
    # Manufacturing KPIs
    # -------------------------------------------------------------------------

    @api.model
    def get_manufacturing_data(self):
        MO = self.env['mrp.production']

        draft_count     = MO.search_count([('state', '=', 'draft')])
        confirmed_count = MO.search_count([('state', '=', 'confirmed')])
        progress_count  = MO.search_count([('state', 'in', ['progress', 'to_close'])])
        done_count      = MO.search_count([('state', '=', 'done')])
        cancel_count    = MO.search_count([('state', '=', 'cancel')])
        total_count     = draft_count + confirmed_count + progress_count + done_count + cancel_count

        today = date.today()
        overdue_count = MO.search_count([
            ('state', 'not in', ['done', 'cancel']),
            ('date_finished', '<', fields.Datetime.now()),
            ('date_finished', '!=', False),
        ])
        today_count = MO.search_count([
            ('date_start', '>=', fields.Datetime.to_datetime(str(today) + ' 00:00:00')),
            ('date_start', '<=', fields.Datetime.to_datetime(str(today) + ' 23:59:59')),
        ])

        # This month done
        month_start = today.replace(day=1)
        month_done = MO.search_count([
            ('state', '=', 'done'),
            ('date_finished', '>=', fields.Datetime.to_datetime(str(month_start) + ' 00:00:00')),
        ])

        # Monthly chart data
        months = self._get_month_labels(6)
        chart_labels    = [m['label'] for m in months]
        chart_confirmed = []
        chart_done_list = []
        for m in months:
            chart_confirmed.append(MO.search_count([
                ('state', 'in', ['confirmed', 'progress', 'to_close']),
                ('date_start', '>=', m['start']),
                ('date_start', '<=', m['end']),
            ]))
            chart_done_list.append(MO.search_count([
                ('state', '=', 'done'),
                ('date_finished', '>=', m['start']),
                ('date_finished', '<=', m['end']),
            ]))

        # Recent manufacturing orders (last 10)
        recent_orders = MO.search([], order='id desc', limit=10)
        recent = []
        for o in recent_orders:
            recent.append({
                'id': o.id,
                'name': o.name,
                'product': o.product_id.display_name or '',
                'qty': o.product_qty,
                'uom': o.product_uom_id.name or '',
                'state': o.state,
                'state_label': dict(o._fields['state'].selection).get(o.state, o.state),
                'date': o.date_start.strftime('%d %b %Y') if o.date_start else '',
                'workcenter': o.workorder_ids[0].workcenter_id.name if o.workorder_ids else '',
            })

        # Workcenter utilization (top 5 by workorder count)
        WorkOrder = self.env['mrp.workorder']
        workcenters_data = []
        for wc in self.env['mrp.workcenter'].search([], limit=5):
            wc_count = WorkOrder.search_count([('workcenter_id', '=', wc.id)])
            wc_done  = WorkOrder.search_count([('workcenter_id', '=', wc.id), ('state', '=', 'done')])
            if wc_count:
                workcenters_data.append({
                    'name': wc.name,
                    'total': wc_count,
                    'done': wc_done,
                    'pct': round(wc_done / wc_count * 100) if wc_count else 0,
                })

        return {
            'draft': draft_count,
            'confirmed': confirmed_count,
            'progress': progress_count,
            'done': done_count,
            'cancel': cancel_count,
            'total': total_count,
            'overdue': overdue_count,
            'today': today_count,
            'month_done': month_done,
            'chart_labels': chart_labels,
            'chart_confirmed': chart_confirmed,
            'chart_done': chart_done_list,
            'recent_orders': recent,
            'workcenters': workcenters_data,
        }

    # -------------------------------------------------------------------------
    # Sales KPIs
    # -------------------------------------------------------------------------

    @api.model
    def get_sales_data(self):
        SO = self.env['sale.order']

        quotation_count = SO.search_count([('state', '=', 'draft')])
        sent_count      = SO.search_count([('state', '=', 'sent')])
        sale_count      = SO.search_count([('state', '=', 'sale')])
        done_count      = SO.search_count([('state', '=', 'done')])
        cancel_count    = SO.search_count([('state', '=', 'cancel')])
        total_count     = quotation_count + sent_count + sale_count + done_count + cancel_count

        confirmed_orders = SO.search([('state', 'in', ['sale', 'done'])])
        confirmed_amount = sum(confirmed_orders.mapped('amount_total'))

        to_invoice_count = SO.search_count([
            ('state', 'in', ['sale', 'done']),
            ('invoice_status', '=', 'to invoice'),
        ])
        overdue_count = SO.search_count([
            ('state', 'in', ['draft', 'sent', 'sale']),
            ('commitment_date', '<', fields.Datetime.now()),
            ('commitment_date', '!=', False),
        ])

        today      = date.today()
        month_start = today.replace(day=1)
        month_orders = SO.search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', fields.Datetime.to_datetime(str(month_start) + ' 00:00:00')),
        ])
        month_amount = sum(month_orders.mapped('amount_total'))
        month_count  = len(month_orders)

        # Average order value
        avg_order_val = round(confirmed_amount / len(confirmed_orders), 2) if confirmed_orders else 0.0

        # Top 5 customers by order total
        from collections import defaultdict
        customer_totals = defaultdict(float)
        for o in confirmed_orders:
            customer_totals[o.partner_id.name or 'Unknown'] += o.amount_total
        top_customers = sorted(customer_totals.items(), key=lambda x: -x[1])[:5]

        # Monthly chart data
        months = self._get_month_labels(6)
        chart_labels = [m['label'] for m in months]
        chart_orders = []
        chart_amount = []
        for m in months:
            mo = SO.search([
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', m['start']),
                ('date_order', '<=', m['end']),
            ])
            chart_orders.append(len(mo))
            chart_amount.append(round(sum(mo.mapped('amount_total')), 2))

        # Recent orders (last 10)
        recent_so = SO.search([], order='id desc', limit=10)
        recent = []
        for o in recent_so:
            recent.append({
                'id': o.id,
                'name': o.name,
                'partner': o.partner_id.name or '',
                'amount': round(o.amount_total, 2),
                'state': o.state,
                'state_label': dict(o._fields['state'].selection).get(o.state, o.state),
                'date': o.date_order.strftime('%d %b %Y') if o.date_order else '',
                'invoice_status': o.invoice_status,
            })

        currency_symbol = self.env.company.currency_id.symbol or '$'

        return {
            'quotation': quotation_count,
            'sent': sent_count,
            'sale': sale_count,
            'done': done_count,
            'cancel': cancel_count,
            'total': total_count,
            'confirmed_amount': confirmed_amount,
            'to_invoice': to_invoice_count,
            'overdue': overdue_count,
            'month_amount': month_amount,
            'month_count': month_count,
            'avg_order_val': avg_order_val,
            'currency_symbol': currency_symbol,
            'chart_labels': chart_labels,
            'chart_orders': chart_orders,
            'chart_amount': chart_amount,
            'recent_orders': recent,
            'top_customers': [{'name': k, 'amount': v} for k, v in top_customers],
        }

    # -------------------------------------------------------------------------
    # Purchase KPIs
    # -------------------------------------------------------------------------

    @api.model
    def get_purchase_data(self):
        PO = self.env['purchase.order']

        draft_count    = PO.search_count([('state', '=', 'draft')])
        sent_count     = PO.search_count([('state', '=', 'sent')])
        purchase_count = PO.search_count([('state', '=', 'purchase')])
        done_count     = PO.search_count([('state', '=', 'done')])
        cancel_count   = PO.search_count([('state', '=', 'cancel')])
        total_count    = draft_count + sent_count + purchase_count + done_count + cancel_count

        confirmed_orders = PO.search([('state', 'in', ['purchase', 'done'])])
        confirmed_amount = sum(confirmed_orders.mapped('amount_total'))

        to_bill_count = PO.search_count([
            ('state', 'in', ['purchase', 'done']),
            ('invoice_status', '=', 'to invoice'),
        ])
        today       = date.today()
        month_start = today.replace(day=1)
        overdue_count = PO.search_count([
            ('state', 'in', ['draft', 'sent', 'purchase']),
            ('date_planned', '<', fields.Datetime.now()),
            ('date_planned', '!=', False),
        ])
        month_orders = PO.search([
            ('state', 'in', ['purchase', 'done']),
            ('date_order', '>=', fields.Datetime.to_datetime(str(month_start) + ' 00:00:00')),
        ])
        month_amount = sum(month_orders.mapped('amount_total'))
        month_count  = len(month_orders)

        # Average order value
        avg_order_val = round(confirmed_amount / len(confirmed_orders), 2) if confirmed_orders else 0.0

        # Top 5 vendors by purchase total
        from collections import defaultdict
        vendor_totals = defaultdict(float)
        for o in confirmed_orders:
            vendor_totals[o.partner_id.name or 'Unknown'] += o.amount_total
        top_vendors = sorted(vendor_totals.items(), key=lambda x: -x[1])[:5]

        # Monthly chart data
        months = self._get_month_labels(6)
        chart_labels = [m['label'] for m in months]
        chart_orders = []
        chart_amount = []
        for m in months:
            po = PO.search([
                ('state', 'in', ['purchase', 'done']),
                ('date_order', '>=', m['start']),
                ('date_order', '<=', m['end']),
            ])
            chart_orders.append(len(po))
            chart_amount.append(round(sum(po.mapped('amount_total')), 2))

        # Recent orders (last 10)
        recent_po = PO.search([], order='id desc', limit=10)
        recent = []
        for o in recent_po:
            recent.append({
                'id': o.id,
                'name': o.name,
                'partner': o.partner_id.name or '',
                'amount': round(o.amount_total, 2),
                'state': o.state,
                'state_label': dict(o._fields['state'].selection).get(o.state, o.state),
                'date': o.date_order.strftime('%d %b %Y') if o.date_order else '',
                'invoice_status': o.invoice_status,
            })

        currency_symbol = self.env.company.currency_id.symbol or '$'

        return {
            'draft': draft_count,
            'sent': sent_count,
            'purchase': purchase_count,
            'done': done_count,
            'cancel': cancel_count,
            'total': total_count,
            'confirmed_amount': confirmed_amount,
            'to_bill': to_bill_count,
            'overdue': overdue_count,
            'month_amount': month_amount,
            'month_count': month_count,
            'avg_order_val': avg_order_val,
            'currency_symbol': currency_symbol,
            'chart_labels': chart_labels,
            'chart_orders': chart_orders,
            'chart_amount': chart_amount,
            'recent_orders': recent,
            'top_vendors': [{'name': k, 'amount': v} for k, v in top_vendors],
        }
