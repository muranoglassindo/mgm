# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields
from odoo.http import request
from datetime import datetime

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	accounting_id = fields.Many2one(
		'res.users', string='Accounting')
	verified = fields.Selection([
		('true', 'Verified'),
		('false', 'Not Verified'),
	], string='Verified', default='false')
	source = fields.Selection([
		('sales', 'Sales'),
		('purchase', 'Purchase'),
	], string='Source', default='sales')
	get_move_line = fields.Boolean("GET")
	
	@api.model
	def create(self, vals):
		res = super(StockPicking, self).create(vals)
		date = res.get_month_year()
		res.name = date + self.env['ir.sequence'].next_by_code('increment.number.stock.picking')
		if res.origin:
			# menggunakan pengecekan dia SQ atau Purchasing, karena purchasing gausah ada verifikasinya
			if res.origin.find("SQ") == 0:
				self._cr.execute("""
					SELECT payment_term_name
					FROM sale_order
					WHERE name = '%s'
				""" % (
					res.origin
				))
				payment_term = self._cr.dictfetchall()
				if payment_term[0]['payment_term_name'] in ('Cash On Delivery', 'DP - Cash On Delivery', 'Tempo'):
					res.verified = 'true'
			else:
				res.source = 'purchase'
		return res
	
	def get_month_year(self):
		format = datetime.now().strftime('%Y%m')
		return format
	
	def write(self, vals):
		res = super(StockPicking, self).write(vals)
		if 'get_move_line' in vals:
			if self.source == 'sales':
				lots = []
				id_del = []
				done_ml = []
				done_ml_picking = []
				manufacture = self.env['stock.location.route'].search([('name', '=', 'Manufacture')])
				if self.move_line_ids_without_package:
					for move_line in self.move_line_ids_without_package:
						if manufacture.id in move_line.product_id.route_ids.ids:
							done_ml.append({
								'lot_id': move_line.lot_id.id,
								'qty_done': move_line.qty_done,
								'status': move_line.status,
							})
							id_del.append(move_line.id)
				if id_del:
					lines = self.env['stock.move.line'].search([('id', 'in', id_del)])
					for line in lines:
						line.update({
							'picking_id': False,
							'move_id': False
						})
					# lines.unlink()
				picking_done = self.env['stock.picking'].search([('origin', '=', self.origin), ('state', '=', 'done')])
				for mlp in picking_done.move_line_ids_without_package:
					done_ml_picking.append(mlp.lot_id.id)
				mrps = self.env['mrp.production'].search([('origin', '=', self.origin)])
				for move in self.move_ids_without_package:
					for mrp in mrps:
						for line in mrp.finished_move_line_ids:
							if line.state == 'done' and line.product_id == move.product_id and mrp.width == move.width and mrp.height == move.height and line.lot_id.id not in done_ml_picking:
								lots.append({
									'product_id': line.product_id.id,
									'product_uom_qty': line.qty_done,
									'qty_done': 0,
									'product_uom_id': line.product_uom_id.id,
									'location_id': move.location_id.id,
									'location_dest_id': move.location_dest_id.id,
									'picking_id': move.picking_id.id,
									'move_id': move.id,
									'state': move.state,
									'lot_id': line.lot_id.id
								})
				if lots:
					for lot in lots:
						for done in done_ml:
							if lot['lot_id'] == done['lot_id']:
								lot['qty_done'] = done['qty_done']
								break
						ml = self.env['stock.move.line'].sudo().create({
							'product_id': lot['product_id'],
							'product_uom_qty': lot['product_uom_qty'],
							'qty_done': lot['qty_done'],
							'product_uom_id': lot['product_uom_id'],
							'location_id': lot['location_id'],
							'location_dest_id': lot['location_dest_id'],
							'lot_id': lot['lot_id'],
							'state': lot['state'],
							'status': 'not_new',
							'picking_id': lot['picking_id'],
							'move_id':  lot['move_id']
						})
						ml.sudo().update({
							'product_uom_qty': lot['product_uom_qty']
						})
					for move in self.move_ids_without_package:
						move.reserved_availability = sum([i.product_uom_qty for i in self.env['stock.move.line'].search([('move_id', '=', move.id),('picking_id', '=', move.picking_id.id)])])
		return res
	
class StockMove(models.Model):
	_inherit = 'stock.move'

	routing = fields.Char("Routing", compute='_compute_detail_product', store=True, default="")
	description = fields.Char("Description", compute='_compute_detail_product', store=True, default="")
	reserved_availability = fields.Float(
		'Quantity Reserved', compute='_compute_reserved_availability', store=True,
		digits='Product Unit of Measure',
		readonly=True, help='Quantity that has already been reserved for this move')
	
	@api.depends('product_id')
	def _compute_detail_product(self):
		for move in self:
			move.routing = ""
			move.description = ""
			if move.product_id:
				for attribute in move.product_id.product_template_attribute_value_ids:
					if attribute.attribute_id.name == "Routing":
						move.routing = attribute.name
						routing = request.env['mrp.routing'].search([('name', '=', move.routing)])
						if routing:
							process = move.get_operation(routing)
							desc = ""
							i = 1
							for res in process:
								desc = desc + res
								if i < len(process):
									desc = desc + ", "
								i = i+1
							move.description = desc
	
	def get_operation(self, routing):
		operations = []
		for operation in routing.operation_ids:
			operations.append(operation.name)
		return operations