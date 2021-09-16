from odoo import api, fields, models, _
from datetime import datetime, timedelta
from itertools import groupby
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from odoo.http import request
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	skdu_so_customer = fields.Binary(string="SKDU", related='partner_id.skdu_customer', help='SKDU customer.')
	skdu_so_customer_file_name = fields.Char(related='partner_id.skdu_customer_file_name')
	
	npwp_so_customer = fields.Binary(string="NPWP", related='partner_id.npwp_customer', help='NPWP customer.')
	npwp_so_customer_file_name = fields.Char(related='partner_id.npwp_customer_file_name')
	
	ktp_so_customer = fields.Binary(string="KTP", related='partner_id.ktp_customer', help='KTP customer.')
	ktp_so_customer_file_name = fields.Char(related='partner_id.ktp_customer_file_name')
	
	siup_so_customer = fields.Binary(string="SIUP", related='partner_id.siup_customer', help='SIUP customer.')
	siup_so_customer_file_name = fields.Char(related='partner_id.siup_customer_file_name')
	
	mou_so_customer = fields.Binary(string="MoU", related='partner_id.mou_customer', help='MoU customer')
	mou_so_customer_file_name = fields.Char(related='partner_id.mou_customer_file_name')
	
	memo_so_customer = fields.Binary(string="Internal Memo", help='Internal memo customer')
	memo_so_customer_file_name = fields.Char(string=_("File Name"))
	
	so_type = fields.Selection([
		('retail', 'Retail'),
		('project', 'Project')
	], default='retail')
	
	is_person = fields.Boolean("Is Person", compute='_compute_partner_type', store=True)
	
	validate_skdu = fields.Boolean("Validate SKDU")
	validate_npwp = fields.Boolean("Validate NPWP")
	validate_ktp = fields.Boolean("Validate KTP")
	validate_siup = fields.Boolean("Validate SIUP")
	validate_mou = fields.Boolean("Validate MoU")
	validate_mi = fields.Boolean("Validate Internal Memo")
	
	amount_disc = fields.Monetary(compute='_compute_amount', string='Discount', store=True)
	amount_undisc = fields.Monetary(compute='_compute_amount', string='Total', store=True)
	gross_profit = fields.Float(compute='_compute_amount', string='Gross Profit (%)', store=True)
	
	on_credit = fields.Boolean("On Credit", readonly=True, related='partner_id.on_credit', help=(_("a sign that the customer still has arrears")))
	
	period = fields.Integer("Period of Time (days)")
	
	person_in_charge = fields.Many2many('res.users', string="Person in Charge", help=(_("Contains users who validate SQ/SO")))
	
	down_payment = fields.Float(_("Down Payment"))

	type_dp = fields.Selection([
		('percentage', '%'),
		('cash', 'Rp')
	], default='cash')
	
	amount_dp = fields.Monetary(compute='_compute_dp_unpaid', string='DP', store=True)
	amount_unpaid = fields.Monetary(compute='_compute_dp_unpaid', string='Unpaid', store=True)
	
	state = fields.Selection([
		('draft', 'Quotation'),
		('sent', 'Quotation Sent'),
		('order', 'Order'),
		('admin', 'Admin Sales'),
		('manager', 'Manager Sales'),
		('fat', 'Staff AR'),
		('fat2', 'Manager FAT'),
		('director', 'Director'),
		('ppic', 'PPIC'),
		('sale', 'Approved'),
		('done', 'Locked'),
		('cancel', 'Cancelled'),
	], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
	
	payment_term_name = fields.Char("Payment Term", compute="_compute_payment_term", store=True)
	
	grand_total_after_disc = fields.Monetary("GRAND TOTAL AFTER DISCOUNT", compute='_compute_amount', store=True)
	
	proccessing_date = fields.Integer("Processing Date", compute="_compute_proccessing_date")
	
	products = fields.Integer("Products", compute="_compute_number_of_products", default=0)

	services = fields.Integer("Services", compute="_compute_number_of_products", default=0)
	
	image = fields.Binary(string='Order Image', help='Order Image.')
	image_name = fields.Char(string=_("File Name"))
	
	proof_of_payment_ids = fields.One2many('proof.of.payments', 'sale_id', string="Proof of Payments")
	
	reason_cancellation_ids = fields.One2many('reason.cancellation', 'sale_id', string="Reason")
	
	customer_complain_ids = fields.One2many('customer.complain', 'sale_id', string="Customer Complain")
	
	im_number = fields.Char("Internal Memo Number")
	
	# untuk menampung nama project (hanya untuk sales project)
	project_name = fields.Char("Project")
	
	# amount_shipping_cost = fields.Monetary("Shipping Cost", compute='compute_shipping_cost', store=True, default=0)
	#
	# shipping_cost = fields.Float("Shipping Cost", default=0)
	#
	# shipping_cost_type = fields.Selection([
	# 	('km', 'Km'),
	# 	('rp', 'Rp')
	# ], default='km')
	
	def unlink(self):
		if (self.env.user.has_group('mgm.mgm_group_manager_sales')):
			res = super(SaleOrder, self).unlink()
		else:
			raise UserError("You can not delete this SQ/SO")
		return res
	
	def write(self, vals):
		if 'memo_so_customer' in vals:
			vals['memo_so_customer_file_name'] = "IM_" + self.partner_id.name + "_" + datetime.now().strftime('%d%m%y')
		if 'image' in vals:
			vals['image_name'] = "Order Image_" + self.partner_id.name + "_" + datetime.now().strftime('%d%m%y')
		if self.state not in ('sent', 'draft', 'order'):
			if 'order_line' in vals or 'user_id' in vals or 'payment_term_id' in vals or 'period' in vals or 'down_payment' in vals or 'type_dp' in vals:
				raise UserError("You can not modify this SQ/SO")
		if self.state in ('sent', 'draft', 'order') and not self.env.user.has_group('mgm.mgm_group_sales'):
			raise UserError("You can not modify this SQ/SO")
		if self.payment_term_name == "Tempo" and 'state' in vals:
			if vals['state'] == "cancel" and self.state == "admin":
				legal = request.env['legal.order'].search([('so_number', '=', self.name)])
				if legal:
					legal.status_sq = "cancel"
		if 'state' in vals:
			if vals['state'] == "sale":
				self.gross_profit_sales()
		return super(SaleOrder, self).write(vals)
	
	# fungsi untuk menampilkan view alasan pembatalan SQ
	def action_cancel_sq(self):
		return {
			'type': 'ir.actions.act_window',
			'name': _('Cancel SQ'),
			'res_model': 'cancel.sq.memory',
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new',
			'context': {
				'default_sale_id': self.id,
			},
		}
	
	@api.constrains('payment_term_id')
	def check_period(self):
		for so in self:
			if so.payment_term_name == "Tempo":
				if so.period <= 0:
					raise UserError("Period of Time must be positive.")
			else:
				so.period = 0
				
	# @api.depends('shipping_cost_type', 'shipping_cost')
	# def compute_shipping_cost(self):
	# 	for res in self:
	# 		self._cr.execute("""
	# 			SELECT list_price
	# 			FROM product_template
	# 			WHERE uom_id = 9
	# 		""")
	# 		shipping_cost = self._cr.dictfetchall()
	# 		if res.shipping_cost_type == "km":
	# 			res.amount_shipping_cost = res.shipping_cost * shipping_cost[0]['list_price']
	# 		elif res.shipping_cost_type == "rp":
	# 			res.amount_shipping_cost = res.shipping_cost
	
	@api.depends('down_payment', 'type_dp', 'amount_total', 'payment_term_id')
	def _compute_dp_unpaid(self):
		for so in self:
			if so.payment_term_id:
				if so.payment_term_id.name == "DP - Cash Before Delivery" or so.payment_term_id.name == "DP - Cash On Delivery" or so.payment_term_id.name == "Tempo":
					if so.payment_term_id.name == "Tempo":
						if so.type_dp == "percentage":
							if 0 <= so.down_payment < 100:
								so.amount_dp = so.amount_total * (so.down_payment / 100)
							else:
								raise UserError("DP must be positive and cannot be more than or equal to 100.")
						else:
							if 0 <= so.down_payment < so.amount_total:
								so.amount_dp = so.down_payment
							else:
								raise UserError("DP must be positive and cannot be more or equal to the grand total.")
					else:
						if so.type_dp == "percentage":
							if 0 < so.down_payment < 100:
								so.amount_dp = so.amount_total * (so.down_payment / 100)
							else:
								raise UserError("DP must be positive and cannot be more than or equal to 100.")
						else:
							if 0 < so.down_payment < so.amount_total:
								so.amount_dp = so.down_payment
							else:
								raise UserError("DP must be positive and cannot be more or equal to the grand total.")
			else:
				so.amount_dp = 0
			so.amount_unpaid = so.amount_total - so.amount_dp
	
	@api.depends('order_line')
	def _compute_number_of_products(self):
		for order in self:
			products = order.products
			services = order.services
			for line in order.order_line:
				if line.product_id.categ_id.name == "Finish Good":
					products = products + line.qty
				elif line.product_id.categ_id.name == "Service":
					if line.product_id.uom_id.name != "km":
						services = services + line.qty
					else:
						services = services + 1
			order.products = products
			order.services = services
	
	@api.depends('date_order','commitment_date')
	def _compute_proccessing_date(self):
		self.proccessing_date = relativedelta(self.commitment_date, self.date_order).days
	
	@api.depends('order_line')
	def _compute_amount(self):
		for so in self:
			disc = 0
			total = 0
			amount = 0
			ppn = 0
			gross_profit = 0
			shipping_cost = 0
			ppn_shipping_cost = 0
			for order_line in so.order_line:
				if order_line.product_id.uom_id.name == "M1" or order_line.product_id.uom_id.name == "M2":
					total = total + (order_line.area * order_line.price_unit)
				else:
					total = total + (order_line.qty * order_line.price_unit)
				disc = disc + order_line.disc_value
				# untuk mendapatkan amount dari tax produk yang pake UoM "Km" : shipping cost
				ppn = ppn + order_line.tax_id.amount * order_line.price_subtotal / 100
				amount = total - disc + ppn
				# mendapatkan harga shipping cost beserta pajaknya agak tidak merubah nilai gross profit sales
				if order_line.product_id.uom_id.name == "km":
					shipping_cost = order_line.price_subtotal
					ppn_shipping_cost = order_line.tax_id.amount * shipping_cost / 100
			so.amount_tax = ppn
			so.amount_disc = disc
			so.amount_undisc = total
			so.amount_total = amount
			so.grand_total_after_disc = total - disc
			if so.margin:
				# TODO: jangan masukin kalau dia itu produk shipping
				modal = so.grand_total_after_disc - shipping_cost - so.margin
				try:
					# gross_profit = (so.margin / modal) * 100
					gross_profit = (100 / modal) * so.margin
				except ZeroDivisionError:
					gross_profit = 0
			so.gross_profit = round(gross_profit, 2)
	
	def gross_profit_sales(self):
		# TODO: knapa depends dan onchange gak ke trigger????
		for so in self:
			if so.user_id.gross_profit != 0:
				so.user_id.gross_profit = (so.user_id.gross_profit + so.gross_profit) / 2
			else:
				so.user_id.gross_profit = so.gross_profit
				
	@api.depends('partner_id')
	def _compute_partner_type(self):
		""" untuk mendapatkan jenis partner, apabila dia personal maka akan bernilai true
        """
		for so in self:
			if (so.partner_id.company_type == "person"):
				so.is_person = True
			else:
				so.is_person = False
	
	@api.depends('payment_term_id')
	def _compute_payment_term(self):
		""" untuk mendapatkan jenis pembayaran
			mengembalikan nama metode pembayaran
        """
		for so in self:
			if so.payment_term_id:
				so.payment_term_name = so.payment_term_id.name
			else:
				so.payment_term_name = ""
	
				
	def raise_validation(self, text):
		raise UserError(text)
	
	def check_requirements(self, so):
		position = ""
		text = ""
		if so.so_type == 'retail':
			if (so.state == 'admin'):
				position = 'manager'
			elif (so.state == 'manager'):
				position = 'fat'
			elif (so.state == 'fat'):
				position = 'fat2'
			elif (so.state == 'fat2'):
				position = 'ppic'
			
			# if (so.payment_term_name != "Immediate Payment" and so.payment_term_name != "Cash On Delivery"):
			if (so.payment_term_name == "Tempo"):
				if (so.is_person == False):
					if (so.period >= 30):
						if (so.skdu_so_customer != False and so.npwp_so_customer != False and so.ktp_so_customer != False and so.siup_so_customer != False and so.mou_so_customer != False):
							if (so.validate_skdu != False and so.validate_npwp != False and so.validate_ktp != False and so.validate_siup != False and so.validate_mou != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
					else:
						if (so.skdu_so_customer != False and so.npwp_so_customer != False and so.ktp_so_customer != False and so.siup_so_customer != False and so.memo_so_customer != False):
							if (so.validate_skdu != False and so.validate_npwp != False and so.validate_ktp != False and so.validate_siup != False and so.validate_mi != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
				elif (so.is_person == True):
					if (so.period >= 30):
						if (so.npwp_so_customer != False and so.ktp_so_customer != False and so.mou_so_customer != False):
							if (so.validate_npwp != False and so.validate_ktp != False and so.validate_mou != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
					else:
						if (so.npwp_so_customer != False and so.ktp_so_customer != False and so.memo_so_customer != False):
							if (so.validate_npwp != False and so.validate_ktp != False and so.validate_mi != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
			# elif (so.payment_term_name == "Cash Before Delivery" or so.payment_term_name == "DP - Cash Before Delivery"):
			# 	if (so.memo_so_customer != False):
			# 		if (so.validate_mi != False):
			# 			so.set_state(position)
			# 		else:
			# 			# if so.state != "ppic":
			# 			text = (_("Please validate all requirements for this payment method."))
			# 	else:
			# 		text = (_("Please meet all requirements for this payment method."))
			else:
				so.set_state(position)
			
			if (text != ""):
				so.raise_validation(text)
		else:
			if (so.state == 'admin'):
				position = 'fat'
			elif (so.state == 'fat'):
				position = 'fat2'
			elif (so.state == 'fat2'):
				position = 'director'
			elif (so.state == 'director'):
				position = 'ppic'
			# if (so.payment_term_name != "Immediate Payment" and so.payment_term_name != "Cash On Delivery"):
			if (so.payment_term_name == "Tempo"):
				if (so.is_person == False):
					if (so.period >= 30):
						if (so.skdu_so_customer != False and so.npwp_so_customer != False and so.ktp_so_customer != False and so.siup_so_customer != False and so.mou_so_customer != False):
							if (so.validate_skdu != False and so.validate_npwp != False and so.validate_ktp != False and so.validate_siup != False and so.validate_mou != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
					else:
						if (so.skdu_so_customer != False and so.npwp_so_customer != False and so.ktp_so_customer != False and so.siup_so_customer != False):
							if (so.validate_skdu != False and so.validate_npwp != False and so.validate_ktp != False and so.validate_siup != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
				elif (so.is_person == True):
					if (so.period >= 30):
						if (so.npwp_so_customer != False and so.ktp_so_customer != False and so.mou_so_customer != False):
							if (so.validate_npwp != False and so.validate_ktp != False and so.validate_mou != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
					else:
						if (so.npwp_so_customer != False and so.ktp_so_customer != False):
							if (so.validate_npwp != False and so.validate_ktp != False):
								# if so.state == "fat2":
								# 	so.partner_id.on_credit = True
								so.set_state(position)
							else:
								# if so.state != "ppic":
								text = (_("Please validate all requirements for this payment method."))
						else:
							text = (_("Please meet all requirements for this payment method."))
			# elif (so.payment_term_name == "Cash Before Delivery" or so.payment_term_name == "DP - Cash Before Delivery"):
			# 	if (so.memo_so_customer != False):
			# 		if (so.validate_mi != False):
			# 			so.set_state(position)
			# 		else:
			# 			# if so.state != "ppic":
			# 			text = (_("Please validate all requirements for this payment method."))
			# 	else:
			# 		text = (_("Please meet all requirements for this payment method."))
			else:
				so.set_state(position)
			
			if (text != ""):
				so.raise_validation(text)
			
	
	def set_state(self, state):
		self.write({
			'state': state,
			'validate_skdu': False,
			'validate_npwp': False,
			'validate_ktp': False,
			'validate_siup': False,
			'validate_mou': False,
			'validate_mi': False,
		})
		
		if (state not in ('sent', 'draft', 'done', 'cancel')):
			self.person_in_charge = [(4, self.env.user.id)]
		if state == 'admin' and self.payment_term_name == "Tempo" and self.period >= 30:
			lo = request.env['legal.order'].search([('so_number', '=', self.name)])
			if not lo:
				self.create_lo()
			else:
				if lo.status_sq == "cancel":
					lo.status_sq = "open"
				
	def create_lo(self):
		if not self.mou_so_customer:
			street = ""
			street2 = ""
			city = ""
			zip = ""
			country = ""
			if self.partner_id.street:
				street = self.partner_id.street
			if self.partner_id.street2:
				street2 = self.partner_id.street2
			if self.partner_id.city:
				city = self.partner_id.city
			if self.partner_id.zip:
				zip = self.partner_id.zip
			if self.partner_id.country_id:
				country = self.partner_id.country_id.name
			address = street + "\n" + street2 + "\n" + city + " " + zip + "\n" + country
			deadline = datetime.now() + timedelta(days=3)
			legal = self.env['legal.order']
			legal.create({
				'so_number': self.name,
				'status_sq': "open",
				'salesperson': self.user_id.name,
				'address': address,
				'deadline': deadline,
				'partner_id': self.partner_id.id,
				'company_type': self.partner_id.company_type
			})
	
	def action_draft(self):
		cancel = super(SaleOrder, self).action_draft()
		for user in self.person_in_charge:
			if not user.id == self.partner_id.id:
				if not user.has_group('mgm.mgm_group_sales'):
					self.person_in_charge = [(3, user.id)]
				else:
					if user.has_group('mgm.mgm_group_admin_sales') or user.has_group('mgm.mgm_group_manager_sales'):
						self.person_in_charge = [(3, user.id)]
		return cancel
	
	def action_confirm(self):
		for so in self:
			so.check_requirements(so)
			legal = request.env['legal.order'].search([('so_number', '=', self.name)])
			if legal:
				legal.status_sq = "done"
			super(SaleOrder, self).action_confirm()
	
	# @api.model_create_multi
	def action_validate(self):
		# melakukan perubahan state pada SO sesuai dengan persyaratan metode pembayaran yang dipilih
		for so in self:
			if so.payment_term_id:
				if (so.state == 'draft'):
					so.set_state('order')
				elif (so.state == 'order'):
					so.set_state('admin')
				elif (so.state == 'ppic'):
					so.set_state('sale')
				else:
					so.check_requirements(so)
			else:
				text = (_("Please choose a payment method"))
				so.raise_validation(text)
	
	# @api.model_create_multi
	def get_month_year(self):
		format = ""
		for so in self:
			month = so.date_order.strftime('%b')
			year = so.date_order.strftime('%y')
			format = month + "/" + year
		return format
	
	@api.model
	def create(self, vals):
		self.check_admin()
		# if not self.env.user.admin_id:
		# 	text = "Please specify your sales admin."
		# 	self.raise_validation(text)
		# else:
		so = super(SaleOrder, self).create(vals)
		date = so.get_month_year()
		so_type = so.so_type
		if self.env.user.has_group('mgm.mgm_group_sales_retail') and self.env.user.has_group('mgm.mgm_group_sales_project'):
			text = "Sorry you can't do this operation."
			self.raise_validation(text)
		else:
			if self.env.user.has_group('mgm.mgm_group_sales_retail'):
				new_name = "SQ" + "/" + so.user_id.code + "/" + so.user_id.admin_id.code + "/" + date.upper() + "/" + self.env['ir.sequence'].next_by_code('increment.number.sq.so')
			elif self.env.user.has_group('mgm.mgm_group_sales_project'):
				so_type = "project"
				new_name = "SQ" + "/PRO/" + date.upper() + "/" + self.env['ir.sequence'].next_by_code('increment.number.sq.so.project')
		so.write({
			'name': new_name,
			'so_type': so_type,
			'person_in_charge': [(4, self.env.user.id)]
		})
		return so
	
	def check_admin(self):
		if self.env.user.has_group('mgm.mgm_group_sales_retail'):
			if not self.env.user.admin_id:
				text = "Please specify your sales admin."
				self.raise_validation(text)
			
	def _create_invoices(self, grouped=False, final=False):
		"""
		Create the invoice associated to the SO.
		:param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
						(partner_invoice_id, currency)
		:param final: if True, refunds will be generated if necessary
		:returns: list of created invoices
		"""
		if not self.env['account.move'].check_access_rights('create', False):
			try:
				self.check_access_rights('write')
				self.check_access_rule('write')
			except AccessError:
				return self.env['account.move']

		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

		# 1) Create invoices.
		invoice_vals_list = []
		for order in self:
			pending_section = None

			# Invoice values.
			invoice_vals = order._prepare_invoice()

			# Invoice line values (keep only necessary sections).
			for line in order.order_line:
				if line.display_type == 'line_section':
					pending_section = line
					continue
				if float_is_zero(line.qty_to_invoice, precision_digits=precision):
					continue
				if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
					if pending_section:
						invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
						pending_section = None
					invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

			if not invoice_vals['invoice_line_ids']:
				raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

			invoice_vals_list.append(invoice_vals)

		if not invoice_vals_list:
			raise UserError(_(
				'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

		# 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
		if not grouped:
			new_invoice_vals_list = []
			for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
				origins = set()
				payment_refs = set()
				refs = set()
				ref_invoice_vals = None
				for invoice_vals in invoices:
					if not ref_invoice_vals:
						ref_invoice_vals = invoice_vals
					else:
						ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
					origins.add(invoice_vals['invoice_origin'])
					payment_refs.add(invoice_vals['invoice_payment_ref'])
					refs.add(invoice_vals['ref'])
				ref_invoice_vals.update({
					'ref': ', '.join(refs)[:2000],
					'invoice_origin': ', '.join(origins),
					'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
				})
				new_invoice_vals_list.append(ref_invoice_vals)
			invoice_vals_list = new_invoice_vals_list
		moves = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals_list)
		if final:
			moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
		for move in moves:
			move.message_post_with_view('mail.message_origin_link',
				values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
				subtype_id=self.env.ref('mail.mt_note').id
			)
		return moves
	
	def get_number_im(self):
		if self.env.user.has_group('mgm.mgm_group_hr_admin'):
			if not self.im_number:
				self.im_number = self.env['ir.sequence'].next_by_code('increment.number.internal.memo') + "/IM/SLS/MGM/" + datetime.now().strftime('%m/%Y')
		return self.im_number
	
	def get_hr_admin(self):
		hr_admin = False
		if self.env.user.has_group('mgm.mgm_group_hr_admin'):
			hr_admin = self.env.user
		return hr_admin
	
	def _get_daily_report_filename(self):
		daily_report_file_name = "Daily Report - " + datetime.now().strftime('%d %b %Y')
		return daily_report_file_name
			
			

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	
	notes = fields.Char("Notes")
	routing = fields.Char("Routing", compute='_compute_detail', help="Routing Manufactur", store=True, default="-")
	height = fields.Integer("H", help="product height")
	width = fields.Integer("W", help="product width")
	thick = fields.Char("T", compute='_compute_detail', help="product thickness", store=True, default="0")
	area = fields.Float("Area Perimeter", compute='_compute_area', help="product area perimeter")
	add_cost = fields.Selection([
		('ireguler1', 'IREGULER SHAPE (Gambar)'),
		('ireguler2', 'IREGULER SHAPE (Mal)'),
		('oversize1', 'OVERSIZE W > 2440'),
		('oversize2', 'OVERSIZE H > 3048'),
		('oversize3', 'OVERSIZE H > 3660'),
	], string='Add Cost')
	total = fields.Monetary("Total", compute='_compute_total', store=True)
	disc_value = fields.Monetary(compute='_compute_value', string='Disc Value', readonly=True, store=True)
	margin = fields.Float(compute='_product_margin', digits='Product Price', store=True)
	price_subtotal = fields.Monetary(compute='_get_subtotal', string='Subtotal', readonly=True, store=True)
	qty = fields.Float('Qty', required=True, default=1)
	manufactured = fields.Boolean('Manufactured')
	
	@api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
	def _product_margin(self):
		# TODO: ketika produknya shipping cost margin jangan ditambahin, karna shipping cost tidak menambahkan gross profit sales
		for line in self:
			currency = line.order_id.pricelist_id.currency_id
			price = line.purchase_price
			if line.product_id.uom_id.name != "km":
				margin = line.price_subtotal - (price * line.product_uom_qty)
			else:
				margin = 0
			line.margin = currency.round(margin) if currency else margin
	
	@api.onchange('area','qty')
	def compute_qty(self):
		for line in self:
			if line.product_id.uom_id.name == "M1" or line.product_id.uom_id.name == "M2":
				line.product_uom_qty = line.area
			else:
				line.product_uom_qty = line.qty
			
	
	# TODO: Perhitungan price subtotal malah ngambil unit price bukannya total
	def write(self, vals):
		res = super(SaleOrderLine, self).write(vals)
		subtotal = self.total - self.disc_value
		if round(self.price_subtotal, 1) != round(subtotal, 1):
			self.price_subtotal = subtotal
		return res
	
	@api.depends('product_id')
	def _compute_detail(self):
		for product in self:
			# if product.product_uom.name in ('M2', 'M1'):
			product.thick = "0"
			product.routing = "-"
			if product.product_id.product_template_attribute_value_ids:
				for value in product.product_id.product_template_attribute_value_ids:
					if value.attribute_id.name == "Ketebalan":
						product.thick = value.name
					elif value.attribute_id.name == "Routing":
						product.routing = value.name
	
	@api.depends('qty_invoiced')
	def set_payment_for_stock_picking(self):
		for line in self:
			if line.qty_invoiced == line.qty_delivered:
				stock_picking = request.env['stock_picking'].search([('origin', '=', line.order_id.name)])
				stock_picking.payment = True
	
	@api.onchange('height','width','qty','product_id')
	def _compute_area(self):
		for order_line in self:
			if order_line.product_id.uom_id.name == "M2":
				area = (order_line.height * order_line.width * order_line.qty) / 1000000
			elif order_line.product_id.uom_id.name == "M1":
				area = ((order_line.height + order_line.width) * 2 * (order_line.qty / 1000))
			else:
				area = 0
			order_line.area = round(area, 2)
			
	@api.onchange('area','add_cost','qty','price_unit')
	def _compute_total(self):
		# semua bisa diganti tapi untuk yg retail tetap pakai harga jual produk walaupun dia bisa diganti
		for line in self:
			# perhitungan add cost dan unit price untuk sales retail
			# if self.env.user.has_group('mgm.mgm_group_sales_retail'):
			# 	add_cost = line.add_cost
			# 	if add_cost:
			# 		if add_cost == "ireguler2" or add_cost == "oversize3":
			# 			line.price_unit = line.product_id.lst_price + (line.product_id.lst_price * 0.2)
			# 		elif add_cost == "ireguler1" or add_cost == "oversize1" or add_cost == "oversize2":
			# 			line.price_unit = line.product_id.lst_price + (line.product_id.lst_price * 0.1)
			# 	else:
			# 		if line.product_id.uom_id.name != "km":
			# 			line.price_unit = line.product_id.lst_price
			# 	if line.product_id.uom_id.name == "M1" or line.product_id.uom_id.name == "M2":
			# 		line.total = (line.area * line.price_unit)
			# 	else:
			# 		line.total = (line.qty * line.price_unit)
			# elif self.env.user.has_group('mgm.mgm_group_sales_project'):
			add_cost = line.add_cost
			if add_cost:
				if add_cost == "ireguler2" or add_cost == "oversize3":
					line.price_unit = line.price_unit + (line.price_unit * 0.2)
				elif add_cost == "ireguler1" or add_cost == "oversize1" or add_cost == "oversize2":
					line.price_unit = line.price_unit + (line.price_unit * 0.1)
			else:
				if line.product_id.uom_id.name != "km":
					line.price_unit = line.price_unit
			if line.product_id.uom_id.name == "M1" or line.product_id.uom_id.name == "M2":
				line.total = (line.area * line.price_unit)
			else:
				line.total = (line.qty * line.price_unit)
				
	@api.onchange('total', 'disc_value')
	def _get_subtotal(self):
		for order_line in self:
			order_line.price_subtotal = order_line.total - order_line.disc_value
	
	@api.depends('discount', 'total')
	def _compute_value(self):
		for order_line in self:
			order_line.disc_value = order_line.total * (order_line.discount / 100)
	
	def _prepare_invoice_line(self):
		"""
		Prepare the dict of values to create the new invoice line for a sales order line.

		:param qty: float quantity to invoice
		"""
		self.ensure_one()
		return {
			'display_type': self.display_type,
			'sequence': self.sequence,
			'notes': self.notes,
			'name': self.name,
			'total': self.total,
			'height': self.height,
			'width': self.width,
			'thick': self.thick,
			# quantity diubah untuk menampung nilai area karena pada fungsi asli odoo, subtotal dipengaruhi oleh qty sedangkan mgm bukan quantitynya tp areanya
			'quantity': self.product_uom_qty,
			'qty': self.product_uom_qty,
			'area': self.area,
			'price_unit': self.price_unit,
			'product_id': self.product_id.id,
			'add_cost': self.add_cost,
			'discount': self.discount,
			'disc_value': self.disc_value,
			'product_uom_id': self.product_uom.id,
			'tax_ids': [(6, 0, self.tax_id.ids)],
			'analytic_account_id': self.order_id.analytic_account_id.id,
			'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
			'sale_line_ids': [(4, self.id)],
		}