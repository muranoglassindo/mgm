# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields
from odoo.http import request
from datetime import datetime

class MrpWorkorder(models.Model):
	_inherit = 'mrp.workorder'

	additional_product_wo_ids = fields.One2many('additional.product', 'workorder_id', string="Additional Product")
	
	@api.model
	def create(self,vals):
		# menambahkan data additional produk untuk MO bersangkutan
		res = super(MrpWorkorder, self).create(vals)
		if res.production_id.additional_product_ids:
			for additional_wo in res.production_id.additional_product_ids:
				res.additional_product_wo_ids = [(0, 0, {
					'product_id': additional_wo.product_id.id,
					'product_qty': additional_wo.product_qty / res.qty_production * res.qty_producing
				})]
		return res

class MrpWorkorderLine(models.Model):
	_inherit = 'mrp.workorder.line'
	
	state = fields.Boolean("State")
	
	@api.model
	def create(self,vals):
		res = super(MrpWorkorderLine, self).create(vals)
		if res.raw_workorder_id:
			for component in res.raw_workorder_id.production_id.move_raw_ids:
				if component.product_id == res.product_id:
					value = component.product_uom_qty / (res.raw_workorder_id.qty_producing * res.raw_workorder_id.qty_production)
					# karena area ini decimal jd ada kemungkinan pas dijumlahin gak sama, ini supaya nyamain qty done dengan qty to consumenya
					if res.raw_workorder_id.qty_production - res.raw_workorder_id.qty_produced == 1:
						value = component.product_uom_qty - component.quantity_done
					res.qty_to_consume = value
					res.qty_reserved = value
					res.qty_done = value
			res.check_components()
		return res
	
	def check_components(self):
		"""
			gatau kenapa kadang componen pada WO suka double, ini untuk mengatasi data doublenya
		:return:
		"""
		for res in self:
			if len(res.raw_workorder_id.raw_workorder_line_ids) > len(res.raw_workorder_id.production_id.move_raw_ids):
				product_components_wo = []
				for component_mo in res.raw_workorder_id.production_id.move_raw_ids:
					for component_wo in res.raw_workorder_id.raw_workorder_line_ids:
						if component_mo.product_id == component_wo.product_id:
							if not product_components_wo:
								product_components_wo.append({
									'id': component_wo.id,
									'product_id': component_wo.product_id.id,
									'qty': component_wo.qty_to_consume
								})
								break
							else:
								for component in product_components_wo:
									if component_wo.id != component['id']:
										if len(product_components_wo) < len(res.raw_workorder_id.production_id.move_raw_ids):
											product_components_wo.append({
												'id': component_wo.id,
												'product_id': component_wo.product_id.id,
												'qty': component_wo.qty_to_consume
											})
											break
				
				for res_comp in product_components_wo:
					for component_wo in res.raw_workorder_id.raw_workorder_line_ids:
						if component_wo.id == res_comp['id'] and not component_wo.state:
							component_wo.state = True
							break
				
				for component_wo in res.raw_workorder_id.raw_workorder_line_ids:
					if not component_wo.state:
						component_wo.sudo().unlink()
			
	
	def write(self, vals):
		if 'qty_to_consume' in vals:
			for component in self.raw_workorder_id.production_id.move_raw_ids:
				if component.product_id == self.product_id:
					value = component.product_uom_qty / (self.raw_workorder_id.qty_producing * self.raw_workorder_id.qty_production)
					if self.raw_workorder_id.qty_production - self.raw_workorder_id.qty_produced == 1:
						value = component.product_uom_qty - component.quantity_done
					vals = {
						'qty_to_consume': value,
						'qty_reserved': value,
						'qty_done': value,
					}
		res = super(MrpWorkorderLine, self).write(vals)
		return res