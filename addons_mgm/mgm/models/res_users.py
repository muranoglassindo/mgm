# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields, _
from odoo.http import request


class ResUsers(models.Model):
	_inherit = "res.users"
	
	code = fields.Char(string="Code", required=True)
	admin_id = fields.Many2one('sales.admin', string='Sales Admin')
	signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
	area = fields.Char(string="Area", help='Area for Sales')
	gross_profit = fields.Float(string='Gross Profit (%)', default=0)
	
	@api.model
	def create(self, vals):
		# akan membuat sales admin apabila user yang sedang dibuat merupaka admin sales
		""" Automatically subscribe employee users to default digest if activated """
		user = super(ResUsers, self).create(vals)
		if (user.has_group('mgm.mgm_group_admin_sales')):
			if not (user.has_group('mgm.mgm_group_manager_sales')) and not (user.has_group('mgm.mgm_group_hr_admin')):
				admin = self.env['sales.admin']
				admin.create({
					'name': user.name,
					'code': user.code
				})
		return user
	
	def write(self, vals):
		# update sales admin apabila user yang di edit merupakan user admin sales, update apabila codenya sama dan buat baru apabila codenya berbeda
		""" Trigger automatic subscription based on updated user groups """
		user = super(ResUsers, self).write(vals)
		if (self.has_group('mgm.mgm_group_admin_sales')):
			if not (self.has_group('mgm.mgm_group_manager_sales')) and not (self.has_group('mgm.mgm_group_hr_admin')):
				admin = request.env['sales.admin'].search([('code', '=', self.code)])
				if not admin:
					admin = self.env['sales.admin']
					admin.create({
						'name': user.name,
						'code': user.code
					})
				else:
					if vals.get('name') != None:
						admin.name = self.name
		return user
	
	def unlink(self):
		if (self.has_group('mgm.mgm_group_admin_sales')):
			if not (self.has_group('mgm.mgm_group_manager_sales')) and not (self.has_group('mgm.mgm_group_hr_admin')):
				admin = request.env['sales.admin'].search([('code', '=', self.code)])
				admin.unlink()
		res = super(ResUsers, self).unlink()
		return res
	
	@api.model
	def reset_gross_profit(self):
		self._cr.execute("""
			SELECT id
			FROM res_users
		""")
		users = self._cr.dictfetchall()
		for user in users:
			if fields.Date.today().day == 20:
				self._cr.execute("""
					UPDATE res_users
					SET gross_profit = 0
					WHERE id = '%s'
                    """ % (
					user['id'],
				))