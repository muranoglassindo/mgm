# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"
	_description = "Sales Advance Payment Invoice"

	notes = fields.Char("Notes")
	height = fields.Integer("H", help="product height")
	width = fields.Integer("W", help="product width")
	thick = fields.Char("T", help="product thickness")
	area = fields.Float("Area Perimeter", help="product area perimeter")
	add_cost = fields.Selection([
		('ireguler1', 'IREGULER SHAPE (Gambar)'),
		('ireguler2', 'IREGULER SHAPE (Mal)'),
		('oversize1', 'OVERSIZE W > 2440'),
		('oversize2', 'OVERSIZE H > 3048'),
		('oversize3', 'OVERSIZE H > 3660'),
	], string='Add Cost')
	total = fields.Monetary("Total")
	unit_price = fields.Monetary("Unit Price")
	disc_value = fields.Monetary(string='Disc Value', readonly=True, store=True)
	price_subtotal = fields.Monetary(string='Sub Total', readonly=True, store=True)



	def create_invoices(self):
		sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

		if self.advance_payment_method == 'delivered':
			sale_orders._create_invoices(final=self.deduct_down_payments)
		else:
			# Create deposit product if necessary
			if not self.product_id:
				vals = self._prepare_deposit_product()
				self.product_id = self.env['product.product'].create(vals)
				self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

			sale_line_obj = self.env['sale.order.line']
			for order in sale_orders:
				amount, name = self._get_advance_details(order)

				if self.product_id.invoice_policy != 'order':
					raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
				if self.product_id.type != 'service':
					raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
				taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
				if order.fiscal_position_id and taxes:
					tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
				else:
					tax_ids = taxes.ids
				context = {'lang': order.partner_id.lang}
				analytic_tag_ids = []
				for line in order.order_line:
					analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

				so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
				so_line = sale_line_obj.create(so_line_values)
				del context
				self._create_invoice(order, so_line, amount)
		if self._context.get('open_invoices', False):
			return sale_orders.action_view_invoice()
		return {'type': 'ir.actions.act_window_close'}


	def _create_invoice(self, order, so_line, amount):
		if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
			raise UserError(_('The value of the down payment amount must be positive.'))

		amount, name = self._get_advance_details(order)

		invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)

		if order.fiscal_position_id:
			invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
		invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
		invoice.message_post_with_view('mail.message_origin_link',
			values={'self': invoice, 'origin': order},
			subtype_id=self.env.ref('mail.mt_note').id)
		return invoice

	def _prepare_invoice_values(self, order, name, amount, so_line):
		invoice_vals = {
			'type': 'out_invoice',
			'invoice_origin': order.name,
			'invoice_user_id': order.user_id.id,
			'narration': order.note,
			'partner_id': order.partner_invoice_id.id,
			'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
			'partner_shipping_id': order.partner_shipping_id.id,
			'currency_id': order.pricelist_id.currency_id.id,
			'invoice_payment_ref': order.client_order_ref,
			'invoice_payment_term_id': order.payment_term_id.id,
			'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
			'team_id': order.team_id.id,
			'campaign_id': order.campaign_id.id,
			'medium_id': order.medium_id.id,
			'source_id': order.source_id.id,
			'invoice_line_ids': [(0, 0, {
				'notes': self.notes,
				'name': name,
				'price_unit': amount,
				'height': self.height,
				'width': self.width,
				'thick': self.thick,
				'quantity': 1.0,
				'area': self.area,
				'product_id': self.product_id.id,
				'add_cost': self.add_cost,
				'disc_value': self.disc_value,
				'price_subtotal': self.price_subtotal,
				'product_uom_id': so_line.product_uom.id,
				'tax_ids': [(6, 0, so_line.tax_id.ids)],
				'sale_line_ids': [(6, 0, [so_line.id])],
				'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
				'analytic_account_id': order.analytic_account_id.id or False,
			})],
		}

		return invoice_vals