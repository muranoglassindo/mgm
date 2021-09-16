from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime, timedelta

class ProofOfPayments(models.Model):
	_name = 'proof.of.payments'
	
	proof_of_payment = fields.Binary(string='Proof of Payment', help='Proof of Payment.')
	proof_of_payment_name = fields.Char(string=_("File Name"))
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	account_move_id = fields.Many2one('account.move', 'Account Move')
	
	@api.model
	def create(self, vals):
		res = super(ProofOfPayments, self).create(vals)
		if res.sale_id:
			res.proof_of_payment_name = "Proof of Payment_" + res.sale_id.partner_id.name + "_" + datetime.now().strftime('%d%m%y')
			if res.sale_id.invoice_ids:
				for inv in res.sale_id.invoice_ids:
					inv.set_proof_of_payments(res)
		elif res.account_move_id:
			res.proof_of_payment_name = "Proof of Payment_" + res.account_move_id.partner_id.name + "_" + datetime.now().strftime('%d%m%y')
		return res