from odoo import models, fields, api, _

class CanselSq(models.TransientModel):
	_name = 'cancel.sq.memory'
	
	sale_id = fields.Many2one('sale.order', 'Source', required=True)
	reason = fields.Text("Reason", required=True)
	
	def action_cancel_sq(self):
		"""
		Close the specified SQ.
		:return:
		"""
		self.env['reason.cancellation'].create({
			'sale_id': self.sale_id.id,
			'user_id': self.env.user.id,
			'reason': self.reason,
			'state': self.sale_id.state
		})
		self.sale_id.action_cancel()

