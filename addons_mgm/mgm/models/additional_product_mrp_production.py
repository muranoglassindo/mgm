from odoo import api, fields, models, _

class AdditionalProduct(models.Model):
	_name = 'additional.product'
	_rec_name = 'product_id'
	
	product_id = fields.Many2one('product.product', 'Product')
	product_qty = fields.Float(string='To Consume', help="The quantity required for all products to be processed.")
	consumed = fields.Float(string='Consumed')
	production_id = fields.Many2one('mrp.production', 'Production', invisible=True)
	workorder_id = fields.Many2one('mrp.workorder', 'Work Order', invisible=True)