from odoo import api, fields, models, _
from odoo.http import request
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = "account.move"
	
	period = fields.Integer("Period of Time (days)")
	payment_term_name = fields.Char("Payment term Name", related='invoice_payment_term_id.name')
	amount_disc = fields.Monetary(string='Discount', readonly=True, store=True)
	amount_undisc = fields.Monetary(string='Total', readonly=True, store=True)
	amount_tax = fields.Monetary(string='PPN', readonly=True, store=True)
	grand_total_after_disc = fields.Monetary("GRAND TOTAL AFTER DISCOUNT", compute='_compute_amount')
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	paid_off = fields.Boolean("Paid Off", compute='_compute_paid_off')
	proof_of_payments = fields.One2many('proof.of.payments', 'account_move_id', string="Proof of Payments")
	amount_dp = fields.Monetary('Down Payments')
	
	@api.model
	def create(self,vals):
		res = super(AccountMove, self).create(vals)
		res.partner_id.on_credit = True
		if res.invoice_origin:
			if res.journal_id.name == "Customer Invoices":
				so = request.env['sale.order'].search([('name', '=', res.invoice_origin)])
				if so:
					due_date = res.due_date(so)
					res.invoice_date_due = due_date
					res.sale_id = so.id
					if so.payment_term_name == "Tempo":
						res.period = so.period
					if res.sale_id.proof_of_payment_ids:
						res.set_proof_of_payments(res.sale_id.proof_of_payment_ids)
					if so.amount_dp:
						res.amount_dp = so.amount_dp
			elif res.journal_id.name == "Vendor Bills":
				po = request.env['purchase.order'].search([('name', '=', res.invoice_origin)])
				if po:
					due_date = res.due_date_po(po)
					res.invoice_date_due = due_date
					if po.payment_term_name == "Tempo":
						res.period = po.period
					for line_po in po.order_line:
						for line_inv in res.invoice_line_ids:
							if line_inv.product_id == line_po.product_id and line_inv.height == 0 and line_inv.width == 0 and line_inv.qty == 0:
								line_inv.height = line_po.height
								line_inv.width = line_po.width
								line_inv.thick = line_po.thick
								line_inv.qty = line_po.product_qty
								line_inv.quantity = line_po.product_qty
								line_inv.area = line_po.area
								line_inv.total = line_po.price_subtotal
								break
			return res
	
	@api.onchange('journal_id', 'partner_id')
	def set_line_ids(self):
		"""
			mengisi data order line ketika create bill (Purchase)
		:return:
		"""
		for res in self:
			if res.journal_id.name == "Vendor Bills":
				po = request.env['purchase.order'].search([('name', '=', res.invoice_origin)])
				if po:
					for line_po in po.order_line:
						for line_inv in res.invoice_line_ids:
							if line_inv.product_id == line_po.product_id and line_inv.height == 0 and line_inv.width == 0 and line_inv.qty == 0:
								line_inv.height = line_po.height
								line_inv.width = line_po.width
								line_inv.thick = line_po.thick
								line_inv.qty = line_po.product_qty
								line_inv.quantity = line_po.product_qty
								line_inv.area = line_po.area
								line_inv.total = line_po.price_subtotal
								if po.invoice_status == "to invoice":
									line_inv.purchase_line_id.qty_received = line_po.product_qty
								print(res.amount_tax)
								break
	
	
	def set_proof_of_payments(self, proof):
		for res in proof:
			self.proof_of_payments = [(4, res.id)]
	
	def write(self,vals):
		# mengubah due date disesuaikan dengan metode pembayaran yang dipilih
		if self.state == "posted":
			inv_number = "MGM" + datetime.now().strftime('%y') + "-" + datetime.now().strftime('%m') + "-" + self.env['ir.sequence'].next_by_code('increment.number.inv')
			vals['name'] = inv_number
		if self.sale_id:
			due_date = self.due_date(self.sale_id)
			vals['invoice_date_due'] = due_date
		res = super(AccountMove, self).write(vals)
		return res
	
	def due_date(self, so):
		# mengambil tanggal due date dari SQ/SO sesuai dengan metode pembayaran
		# return : tanggal jatuh tempo
		delivery = request.env['stock.picking'].search([('origin', '=', so.name), ('state', 'not in', ['done', 'cancel'])])
		if delivery:
			for do in delivery:
				if so.payment_term_name == "Tempo":
					due_date = do.scheduled_date + timedelta(days=so.period)
				else:
					due_date = do.scheduled_date
		else:
			raise ValidationError("Error. delivery has been completed.")
		return due_date
	
	def due_date_po(self, po):
		# mengambil tanggal due date dari SQ/SO sesuai dengan metode pembayaran
		# return : tanggal jatuh tempo
		delivery = request.env['stock.picking'].search([('origin', '=', po.name), ('state', 'not in', ['cancel'])])
		if delivery:
			for do in delivery:
				if po.payment_term_name == "Tempo":
					due_date = do.scheduled_date + timedelta(days=po.period)
				else:
					due_date = do.scheduled_date
		else:
			raise ValidationError("Error. delivery has been cancel.")
		return due_date
	
	def _compute_amount(self):
		res = super(AccountMove, self)._compute_amount()
		for inv in self:
			if inv.sale_id:
				# if inv.invoice_payment_state == "paid":
				# 	amount_total = 0
				amount_due = 0
				amount_total = 0
				total_so = inv.sale_id.amount_total
				amount_due = amount_due + inv.amount_residual_signed
				amount_total = amount_total + inv.amount_total
				if amount_due == 0 and round(amount_total,2) == round(total_so,2):
					# verifikasi DO
					self._cr.execute("""
						SELECT * FROM stock_picking
						WHERE origin = '%s' and state not in ('done','cancel')
					""" % inv.sale_id.name)
					stock_picking = self._cr.dictfetchall()
					if stock_picking:
						for res in stock_picking:
							if res['verified'] == 'false':
								self._cr.execute("""
									UPDATE stock_picking
									SET verified = 'true', accounting_id = '%s'
									WHERE id = '%s'
								""" % (
									self.env.user.id, res['id']
								))
					# Check On Credit Customer
					# self._cr.execute("""
					# 	SELECT id,on_credit from res_partner
					# 	WHERE name = '%s'
					# """ % inv.invoice_partner_display_name)
					# partner_id = self._cr.dictfetchall()
					
					self._cr.execute("""
						SELECT sum(amount_residual_signed)
						FROM account_move
						WHERE partner_id = '%s' and id != '%s'
					""" % (
						inv.partner_id.id,
						inv.id
					))
					amount_due = self._cr.dictfetchall()
					if amount_due[0]['sum'] == 0 and inv.partner_id.on_credit:
						self._cr.execute("""
							UPDATE res_partner
							SET on_credit = 'false'
							WHERE id = '%s'
						""" % (
							inv.partner_id.id
						))
		return res
	
	def get_balance_payment(self):
		for inv in self:
			if inv.amount_dp != 0:
				balance_payment = inv.amount_total - inv.amount_dp
			else:
				balance_payment = inv.amount_total
			return balance_payment
	
	def get_director(self):
		users = self.env['res.users'].search([('code', '=', 'DIR')])
		for user in users:
			if user.has_group('mgm.mgm_group_director'):
				return user

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"
	
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
	qty = fields.Integer("Qty", help="product qty")
	disc_value = fields.Monetary(string='Disc Value', readonly=True, store=True)