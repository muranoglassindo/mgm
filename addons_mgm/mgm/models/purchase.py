from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'
	
	revision = fields.Integer("Revision", default=0)
	approved_by = fields.Many2one('res.users', string='Approved By')
	quotation_vendor = fields.Binary(string="Quotation Vendor")
	quotation_vendor_file_name = fields.Char(string=_("File Name"))
	state = fields.Selection([
		('draft', 'RFQ'),
		('sent', 'RFQ Sent'),
		('to approve', 'To Approve'),
		('director', 'Director'),
		('purchase', 'Purchase Order'),
		('done', 'Locked'),
		('cancel', 'Cancelled')
	], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
	sppkp = fields.Boolean("SPPKP", related='partner_id.sppkp')
	period = fields.Integer("Period of Time (days)")
	payment_term_name = fields.Char("Payment Term", compute="_compute_payment_term", store=True)
	
	@api.model
	def create(self, vals):
		res = super(PurchaseOrder, self).create(vals)
		date = '%s/%s/%s' % (res.create_date.day, res.create_date.month, res.create_date.year)
		res.name = self.env['ir.sequence'].next_by_code('increment.number.purchase.order') + "/MGM/" + date
		if res.quotation_vendor:
			res.quotation_vendor_file_name = "SQ_" + res.partner_id.name + "_" + datetime.now().strftime('%d%m%y')
		return res
		
	def write(self, vals):
		if 'order_line' in vals:
			vals["revision"] = self.revision + 1
		if 'state' in vals:
			if vals["state"] == "purchase":
				self.approved_by = self.env.user
		if 'quotation_vendor' in vals:
			vals["quotation_vendor_file_name"] = "SQ_" + self.partner_id.name + "_" + datetime.now().strftime('%d%m%y')
		super(PurchaseOrder, self).write(vals)
	
	def action_validate(self):
		for res in self:
			if not res.payment_term_id:
				raise ValidationError("Please fill payment terms for this purchase")
			else:
				res.state = 'director'
	
	def button_confirm(self):
		for order in self:
			if order.state not in ['draft', 'sent', 'director']:
				continue
			order._add_supplier_to_product()
			# Deal with double validation process
			if order.company_id.po_double_validation == 'one_step' \
					or (order.company_id.po_double_validation == 'two_step' \
						and order.amount_total < self.env.company.currency_id._convert(
						order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today())) \
					or order.user_has_groups('purchase.group_purchase_manager'):
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
		return True
	
	def action_view_invoice(self):
		if not self.payment_term_id:
			raise ValidationError("Please fill payment terms for this purchase")
		else:
			if self.payment_term_id.name == "Cash On Delivery" or self.payment_term_id.name == "Tempo":
				if self.check_receipt():
					return super(PurchaseOrder, self).action_view_invoice()
				else:
					raise ValidationError("Bills for the payment method you choose can only be made when the goods have been received")
			elif self.payment_term_id.name == "Immediate Payment" or self.payment_term_id.name == "DP - Cash Before Delivery" or self.payment_term_id.name == "Cash Before Delivery" or self.payment_term_id.name == "DP - Cash On Delivery":
				return super(PurchaseOrder, self).action_view_invoice()
			
	def check_receipt(self):
		receipt = request.env['stock.picking'].search([('origin', '=', self.name), ('state', '=', ['done'])])
		return receipt
	
	@api.depends('payment_term_id')
	def _compute_payment_term(self):
		""" untuk mendapatkan jenis pembayaran
			mengembalikan nama metode pembayaran
        """
		for res in self:
			if res.payment_term_id:
				res.payment_term_name = res.payment_term_id.name
			else:
				res.payment_term_name = ""

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'
	
	height = fields.Integer("H", default=0, help="product height")
	width = fields.Integer("W", default=0, help="product width")
	area = fields.Float("Area Perimeter", compute='_compute_area', help="product area perimeter")
	thick = fields.Char("T", compute='_compute_detail', help="product thickness", store=True, default="0")
	
	@api.onchange('height','width','product_qty','product_id','area')
	def _compute_area(self):
		for order_line in self:
			if order_line.product_id.uom_id.name == "M2":
				area = (order_line.height * order_line.width * order_line.product_qty) / 1000000
				# subtotal = area * order_line.price_unit
			elif order_line.product_id.uom_id.name == "M1":
				area = ((order_line.height + order_line.width) * 2 * (order_line.product_qty / 1000))
				# subtotal = area * order_line.price_unit
			else:
				area = 0
				# subtotal = order_line.product_qty * order_line.price_unit
			order_line.write({
				'area': round(area, 2),
				# 'price_subtotal': subtotal
			})
	
	@api.depends('product_id')
	def _compute_detail(self):
		for product in self:
			# if product.product_uom.name in ('M2', 'M1'):
			product.thick = "0"
			if product.product_id.product_template_attribute_value_ids:
				for value in product.product_id.product_template_attribute_value_ids:
					if value.attribute_id.name == "Ketebalan":
						product.thick = value.name