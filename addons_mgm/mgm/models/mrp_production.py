from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

class MrpProduction(models.Model):
	_inherit = 'mrp.production'
	
	additional_product_ids = fields.One2many('additional.product', 'production_id', string="Additional Product")
	height = fields.Integer("Height", default=0, help="product height")
	width = fields.Integer("Width", default=0, help="product width")
	area = fields.Float("Area Perimeter", default=0, help="product area perimeter")
	image = fields.Image('Image', copy=False, attachment=True, max_width=1024, max_height=1024)
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	description = fields.Char("Description")
	notes = fields.Text("Notes")
	effective_date = fields.Datetime('Effective Date')
	shipping_date = fields.Datetime('Shipping Date', related='sale_id.commitment_date')
	revision = fields.Integer("Revision", default=0)
	sched_id = fields.Char("Sched ID")
	unit_id = fields.Char("Unit ID")
	kog = fields.Char("KOG")
	marking = fields.Selection([
		('temp', 'MGM TEMP'),
		('temp_lami', 'MGM TEMP LAMI'),
		('lami', 'MGM LAMINATED'),
		('heat', 'MGM HEAT STRENGTHED'),
		('curve', 'MGM CURVE TEMPERED'),
	])
	mal = fields.Char("Mal")
	shape = fields.Selection([
		('square', 'SQUARE'),
		('ireguler', 'IREGULER')
	], default='square')
	comment = fields.Char("Order Comment")
	packing = fields.Char("Packing")
	sales_id = fields.Many2one('res.users', 'Sales')
	admin_sales = fields.Char("Admin Sales")
	sale_line_id = fields.Integer("id sales order line", default=0)
	
	
	@api.model
	def create(self, vals):
		# menambahkan width, height serta info lainnya pada produk produksi
		res = super(MrpProduction, self).create(vals)
		sale_order = request.env['sale.order'].search([('name', '=', res.origin)])
		for line in sale_order.order_line:
			if res.sale_line_id == 0 and line.product_id == res.product_id and line.qty == res.product_qty and line.height != res.height and line.width != res.width and not line.manufactured:
				res.sudo().write({
					'sale_line_id': line.id,
					'height': line.height,
					'width': line.width,
					'area': line.product_uom_qty,
					'notes': line.notes,
					'comment': line.notes,
				})
				line.sudo().write({
					'manufactured': True
				})
				break
		process = res.detail_process()
		effective_date = datetime.now().strftime('%Y-%m-%d')
		deadline = 0
		if sale_order.commitment_date:
			deadline = sale_order.commitment_date - timedelta(days=1)
		res.sudo().write({
			'sale_id': sale_order.id,
			'description': process,
			'date_deadline': deadline,
			'date_planned_start': datetime.now(),
			'date_planned_finished': deadline,
			'effective_date': effective_date,
		})
		res.sudo().write({
			'sales_id': res.sale_id.user_id.id,
			'admin_sales': res.sale_id.user_id.user_ids[0].admin_id.name
		})
		return res
	
	# @api.model
	# def create(self, vals):
	# 	# menambahkan width, height serta info lainnya pada produk produksi
	# 	res = super(MrpProduction, self).create(vals)
	# 	self._cr.execute("""
	# 		SELECT id, commitment_date
	# 		FROM sale_order
	# 		WHERE name = '%s'
	# 	""" % (
	# 		res.origin
	# 	))
	# 	order_id = self._cr.dictfetchall()
	# 	self._cr.execute("""
	# 		SELECT id, sale_line_id, product_id, product_qty, width, height
	# 		FROM mrp_production
	# 		WHERE origin = '%s'
	# 	""" % (
	# 		res.origin
	# 	))
	# 	production_ids = self._cr.dictfetchall()
	# 	products = res._get_products(order_id)
	# 	if products:
	# 		for product in products:
	# 			for production in production_ids:
	# 				if production['sale_line_id'] == 0 and production['product_id'] == product['product_id'] and production['product_qty'] == product['qty'] and production['width'] != product['width'] and production['height'] != product['height']:
	# 					self._cr.execute("""
	# 							UPDATE mrp_production
	# 							SET width = '%s', height = '%s', area = '%s', notes = '%s', comment = '%s', product_qty = '%s', sale_line_id = '%s'
	# 							WHERE id = '%s'
	# 						""" % (
	# 						product['width'], product['height'], product['product_uom_qty'], product['notes'], product['notes'], product['qty'], product['id'], production['id']
	# 					))
	# 					break
	# 	process = res.detail_process()
	# 	effective_date = datetime.now().strftime('%Y-%m-%d')
	# 	deadline = 0
	# 	if order_id[0]['commitment_date']:
	# 		deadline = order_id[0]['commitment_date'] - timedelta(days=1)
	# 	res.sudo().write({
	# 		'sale_id': order_id[0]['id'],
	# 		'description': process,
	# 		'date_deadline': deadline,
	# 		'date_planned_start': datetime.now(),
	# 		'date_planned_finished': deadline,
	# 		'effective_date': effective_date,
	# 	})
	# 	res.sudo().write({
	# 		'sales_id': res.sale_id.user_id.id,
	# 		'admin_sales': res.sale_id.user_id.user_ids[0].admin_id.name
	# 	})
	# 	return res
	
	# def _get_products(self, source):
	# 	self._cr.execute("""
	# 		SELECT id, product_id, product_uom_qty, height, width, notes, qty
	# 		FROM sale_order_line
	# 		WHERE order_id='%s'
	# 	""" % (
	# 		source.id
	# 	))
	# 	products = self._cr.dictfetchall()
	# 	return products
	
	def detail_process(self):
		for mrp in self:
			process = mrp.get_operation(mrp.routing_id)
			desc = ""
			i = 1
			for res in process:
				desc = desc + res
				if i < len(process):
					desc = desc + ", "
				i = i+1
			return desc
	
	def get_operation(self, routing):
		operations = []
		for operation in routing.operation_ids:
			operations.append(operation.name)
		return operations
	
	@api.constrains('state')
	def set_date_planned(self):
		for res in self:
			if res.state == 'planned':
				self._cr.execute("""
					UPDATE mrp_production
					SET date_planned_start = '%s',
						date_planned_finished = '%s'
					WHERE id = '%s'
                    """ % (
					datetime.now(),
					res.date_deadline,
					res.id
				))
	
	def write(self, vals):
		if (self.env.user.has_group('mgm.mgm_group_ppic') or self.env.user.has_group('mgm.mgm_group_production')):
			qty = self.product_qty
			res = super(MrpProduction, self).write(vals)
			if 'image' in vals:
				self.write({
					'effective_date': datetime.now().strftime('%Y-%m-%d'),
					'revision': self.revision + 1
				})
			if 'product_qty' in vals:
				self.write({
					'area': self.area / qty * vals['product_qty']
				})
			return res
		else:
			raise ValidationError(_("You can not modify this MO"))
				
	def get_area_per_pcs(self):
		area_per_pcs = 0
		for production in self:
			area_per_pcs = production.area / production.product_qty
			return area_per_pcs
	
	def post_inventory(self):
		res = super(MrpProduction, self).post_inventory()
		# self.change_component()
		return res
	
	def change_component(self):
		done = 0
		for res in self:
			for component in res.move_raw_ids:
				if component.state == "assigned":
					res.move_raw_ids = [(3, component.id)]
				elif component.state == "done":
					component.product_uom_qty = component.quantity_done
			for component_prod in self.bom_id.bom_line_ids:
				uom_qty = res.area - (res.area / res.product_qty * len(res.finished_move_line_ids))
				res.write({
					'move_raw_ids': [
						(0, 0, {
							'product_id': component_prod.product_id.id,
							'name': component_prod.product_id.display_name,
							'product_uom': component_prod.product_id.uom_id.id,
							'product_uom_qty': uom_qty,
							'location_id': 8,
							'location_dest_id': 15,
							# quantity_done=0 (computed)
							'move_line_ids': [(0, 0, {
								'product_id': component_prod.product_id.id,
								'product_uom_id': component_prod.product_id.uom_id.id,
								'location_id': 8,
								'location_dest_id': 15,
								'product_uom_qty': uom_qty,
								'qty_done': 0.0 # -> 1.0
							})] # -> new line with qty=0, qty_done=2
						}),
					],
				})