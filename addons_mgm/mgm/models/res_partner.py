from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.http import request
from datetime import datetime, timedelta

class Partner(models.Model):
	_inherit = 'res.partner'
	
	skdu_customer = fields.Binary("SKDU", help='SKDU customer.')
	skdu_customer_file_name = fields.Char(string=_("File Name"))
	
	npwp_customer = fields.Binary(string='NPWP', help='NPWP customer.')
	npwp_customer_file_name = fields.Char(string=_("File Name"))
	
	ktp_customer = fields.Binary(string='KTP', help='KTP customer.')
	ktp_customer_file_name = fields.Char(string=_("File Name"))
	
	siup_customer = fields.Binary(string='SIUP', help='SIUP customer.')
	siup_customer_file_name = fields.Char(string=_("File Name"))
	
	mou_customer = fields.Binary(string='MoU', help='MoU customer.')
	mou_customer_file_name = fields.Char(string=_("File Name"))
	
	on_credit = fields.Boolean("On Credit", help=(_("a sign that the customer still has arrears")))
	
	sppkp = fields.Boolean("SPPKP", help=(_("a sign that the vendor's product has tax")))
	
	signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
	
	def write(self, vals):
		if 'skdu_customer' in vals:
			vals['skdu_customer_file_name'] = "SKDU_" + self.name + "_" + datetime.now().strftime('%d%m%y')
		if 'npwp_customer' in vals:
			vals['npwp_customer_file_name'] = "NPWP_" + self.name + "_" + datetime.now().strftime('%d%m%y')
		if 'ktp_customer' in vals:
			vals['ktp_customer_file_name'] = "KTP_" + self.name + "_" + datetime.now().strftime('%d%m%y')
		if 'siup_customer' in vals:
			vals['siup_customer_file_name'] = "SIUP_" + self.name + "_" + datetime.now().strftime('%d%m%y')
		if 'mou_customer' in vals:
			vals['mou_customer_file_name'] = "MoU_" + self.name + "_" + datetime.now().strftime('%d%m%y')
		res = super(Partner, self).write(vals)
		legals = request.env['legal.order'].search([('partner_id', '=', self.id)])
		for legal in legals:
			if 'skdu_customer' in vals:
				legal.write({
					'skdu_lo_customer': vals['skdu_customer'],
					'skdu_lo_customer_file_name': vals['skdu_customer_file_name']
				})
			if 'npwp_customer' in vals:
				legal.write({
					'npwp_lo_customer': vals['npwp_customer'],
					'npwp_lo_customer_file_name': vals['npwp_customer_file_name']
				})
			if 'ktp_customer' in vals:
				legal.write({
					'ktp_lo_customer': vals['ktp_customer'],
					'ktp_lo_customer_file_name': vals['ktp_customer_file_name']
				})
			if 'siup_customer' in vals:
				legal.write({
					'siup_lo_customer': vals['siup_customer'],
					'siup_lo_customer_file_name': vals['siup_customer_file_name']
				})
			if self.company_type == 'company':
				if legal.skdu_lo_customer and legal.npwp_lo_customer and legal.ktp_lo_customer and legal.siup_lo_customer:
					legal.state = 'ready'
					legal.ready = True
			else:
				if legal.npwp_lo_customer and legal.ktp_lo_customer:
					legal.state = 'ready'
					legal.ready = True
			
			if legal.state != "cancel":
				legal.check_state()
		return res