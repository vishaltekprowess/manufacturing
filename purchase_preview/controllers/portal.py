from odoo import http, _
from odoo.http import request
from odoo.addons.purchase.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError

class PurchasePreviewPortal(CustomerPortal):
    @http.route(['/my/purchase/<int:order_id>/manager_confirm'], type='http', auth="public", website=True)
    def portal_my_purchase_order_manager_confirm(self, order_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('purchase.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Check if current user is the manager
        if request.env.user == order_sudo.manager_id or (kw.get('pid') and int(kw.get('pid')) == order_sudo.manager_id.partner_id.id):
            order_sudo.sudo().write({'is_manager_confirmed': True})
            order_sudo.message_post(body=_("Order confirmed by Manager."))

        return request.redirect(order_sudo.get_portal_url(query_string=f"&pid={kw.get('pid')}&hash={kw.get('hash')}" if kw.get('pid') else ""))
