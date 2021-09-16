# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import models, api, fields
from odoo.http import request
from datetime import datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
	_inherit = 'stock.move'
	
	area = fields.Float("Area Perimeter", help="product area perimeter")
	height = fields.Integer("H", help="product height")
	width = fields.Integer("W", help="product width")
	qty = fields.Integer("Qty", help="product quantity")
	
	@api.model
	def create(self, vals):
		res = super(StockMove, self).create(vals)
		if res.picking_type_id.name == "Delivery Orders":
			res.write({
				'height': res.sale_line_id.height,
				'width': res.sale_line_id.width,
				'area': res.sale_line_id.area,
				'qty': res.sale_line_id.qty,
				'product_uom_qty': res.sale_line_id.qty
			})
		elif res.picking_type_id.name == "Receipts":
			if res.purchase_line_id.product_id.uom_id.name == "M2" or res.purchase_line_id.product_id.uom_id.name == "M1":
				qty = res.purchase_line_id.area
			else:
				qty = res.purchase_line_id.product_qty
			res.write({
				'height': res.purchase_line_id.height,
				'width': res.purchase_line_id.width,
				'area': res.purchase_line_id.area,
				'qty': res.purchase_line_id.product_qty,
				'product_uom_qty': qty,
			})
		elif res.picking_type_id.name == "Manufacturing":
			if res.raw_material_production_id:
				production = res.raw_material_production_id
				if production.bom_id:
					components = [{}]
					# mendapatkan data component BoM dari produk yang akan di produksi
					for component in production.move_raw_ids:
						components.append({
							"id": component.product_id.id,
							"qty": component.product_qty
						})
					while {} in components:
						components.remove({})
					for component in components:
						if component['id'] and component['id'] == res.product_id.id:
							self._cr.execute("""
								UPDATE stock_move
								SET product_qty = '%s', product_uom_qty = '%s'
								WHERE raw_material_production_id = '%s' and product_id = '%s'
							""" % (
								int(component['qty']) / res.raw_material_production_id.product_qty * res.raw_material_production_id.area,
								int(component['qty']) / res.raw_material_production_id.product_qty * res.raw_material_production_id.area,
								res.raw_material_production_id.id,
								component['id']
							))
		return res


class StockMoveLine(models.Model):
	_inherit = 'stock.move.line'
	
	status = fields.Selection([
		('new', 'New'),
		('not_new', 'Not New'),
	], default='new')
	
	
	@api.model
	def create(self, vals):
		move_id = request.env['stock.move'].search([('id', '=', vals['move_id'])])
		if move_id.picking_type_id.name == "Delivery Orders":
			product_uom_qty = move_id.sale_line_id.qty - move_id.sale_line_id.qty_delivered
			move_id.write({
				'qty': product_uom_qty,
				'product_uom_qty': product_uom_qty
			})
			vals['product_uom_qty'] = product_uom_qty
		res = super(StockMoveLine, self).create(vals)
		if move_id.picking_type_id.name == "Delivery Orders":
			if not res.picking_id.get_move_line or res.status == 'new':
				res.picking_id.get_move_line = True
		if res.move_id.production_id:
			total = 0
			for product in res.move_id.production_id.finished_move_line_ids:
				total = total + product.qty_done
			for additional in res.move_id.production_id.additional_product_ids:
				additional.consumed = additional.product_qty / res.move_id.production_id.product_qty * total
		# if res.picking_id.picking_type_id.name == "Delivery Orders":
		# 	res.write({
		# 		'product_uom_qty': res.move_id.sale_line_id.qty - res.move_id.sale_line_id.qty_delivered
		# 	})
		return res
	
	def unlink(self):
		res = super(StockMoveLine, self).unlink()
		return res

class StockQuant(models.Model):
	_inherit = 'stock.quant'
	
	@api.model
	def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
		""" Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
		sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
		the *exact same characteristics* otherwise. Typically, this method is called when reserving
		a move or updating a reserved move line. When reserving a chained move, the strict flag
		should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
		anything from the stock, so we disable the flag. When editing a move line, we naturally
		enable the flag, to reflect the reservation according to the edition.
	
		:return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
			was done and how much the system was able to reserve on it
		"""
		self = self.sudo()
		rounding = product_id.uom_id.rounding
		quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
		reserved_quants = []
		
		if float_compare(quantity, 0, precision_rounding=rounding) > 0:
			# if we want to reserve
			available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
			if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
				raise UserError(_('It is not possible to reserve more products of %s than you have in stock.') % product_id.display_name)
		elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
			# if we want to unreserve
			available_quantity = sum(quants.mapped('reserved_quantity'))
			# if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
			#     raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.') % product_id.display_name)
		else:
			return reserved_quants
		
		for quant in quants:
			if float_compare(quantity, 0, precision_rounding=rounding) > 0:
				max_quantity_on_quant = quant.quantity - quant.reserved_quantity
				if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
					continue
				max_quantity_on_quant = min(max_quantity_on_quant, quantity)
				quant.reserved_quantity += max_quantity_on_quant
				reserved_quants.append((quant, max_quantity_on_quant))
				quantity -= max_quantity_on_quant
				available_quantity -= max_quantity_on_quant
			else:
				max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
				quant.reserved_quantity -= max_quantity_on_quant
				reserved_quants.append((quant, -max_quantity_on_quant))
				quantity += max_quantity_on_quant
				available_quantity += max_quantity_on_quant
			
			if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
				break
		return reserved_quants