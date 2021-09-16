from odoo import api, fields, models, _

class ReasonCancellation(models.Model):
	_name = 'reason.cancellation'
	
	user_id = fields.Many2one('res.users', string='User')
	sale_id = fields.Many2one('sale.order', 'Sale Order')
	reason = fields.Text("Reason For Cancellation")
	state = fields.Selection([
		('draft', 'Quotation'),
		('sent', 'Quotation Sent'),
		('order', 'Order'),
		('admin', 'Admin Sales'),
		('manager', 'Manager Sales'),
		('fat', 'Staff AR'),
		('fat2', 'Manager FAT'),
		('ppic', 'PPIC'),
		('sale', 'Approved'),
		('done', 'Locked'),
		('cancel', 'Cancelled'),
	], string='Status')