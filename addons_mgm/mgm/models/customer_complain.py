from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class CustomerComplain(models.Model):
	_name = 'customer.complain'
	
	name = fields.Char("Name")
	date = fields.Date(string="Date")
	partner_id = fields.Many2one('res.partner', string="Customer", ondelete='cascade')
	sale_id = fields.Many2one('sale.order', 'SQ/SO', required=True)
	report = fields.Text(string="Complaint Details")
	action = fields.Text(string="Corrective and Preventive Action")
	pic = fields.Many2one('res.users', string='PIC & Dept', required=True)
	due_date = fields.Datetime(string="Due Date")
	state = fields.Selection([
		('wip', 'WIP'),
		('done', 'DONE'),
		('not_yet', 'NOT YET')
	], default='wip')
	information = fields.Text(string="Information")
	
	def action_validate(self):
		for res in self:
			if not res.sale_id or not res.pic:
				raise UserError(_('You have to fill in the SQ/SO and PIC.'))
			elif res.state == 'wip':
				res.state = 'done'
			elif res.state == 'not_yet':
				res.state = 'done'
	
	@api.model
	def create(self,vals):
		self._cr.execute("""
			SELECT name FROM sale_order
			WHERE (id = '%s')
			""" % (
			vals['sale_id']
		))
		sq = self._cr.dictfetchall()
		vals['name'] = "Complain Customer - " + sq[0]['name']
		res = super(CustomerComplain, self).create(vals)
		# kaya gini supaya group by per customernya bisa dilakukan, tadinya mau related tp related gabisa dijadiin untuk group seacrh
		res.partner_id = res.sale_id.partner_id
		return res
	
	def write(self, vals):
		if not self.env.user.has_group('mgm.mgm_group_admin_sales'):
			if self.pic.id != self.env.uid:
				raise UserError("You can not modify this Customer Complaint")
			if "pic" in vals:
				raise UserError("You can not modify the PIC of this Customer Complaint")
		if "sale_id" in vals:
			self._cr.execute("""
				SELECT * FROM sale_order
				WHERE (id = '%s')
				""" % (
				vals['sale_id']
			))
			sq = self._cr.dictfetchall()
			vals['name'] = "Complain Customer - " + sq[0]['name']
			vals['partner_id'] = sq[0]['partner_id']
		if "state" in vals and "pic" not in vals:
			if self.pic.id != self.env.uid:
				raise ValidationError(_("Sorry, only the person in charge can confirm this customer complaint."))
		super(CustomerComplain, self).write(vals)
	
	@api.model
	def process_scheduler_queue(self):
		records = self.search([('state', 'not in', ('done', 'not_yet'))])
		for rec in records:
			if rec.due_date and rec.due_date.date() < fields.Date.today():
				self._cr.execute("""
					UPDATE customer_complain
					SET state = '%s'
					WHERE id = '%s'
                    """ % (
					'not_yet',
					rec.id,
				))