from odoo import models, fields, api, _
from xlrd import open_workbook,XLRDError
import base64
from odoo.exceptions import ValidationError
from datetime import datetime

class DairyReportMemory(models.TransientModel):
	_name = 'daily.report.memory'
	_description = 'Daily Report Memory'
	
	type = fields.Selection([
		('sales', 'Laporan Harian Sales'),
		('admin', 'Rekapitulasi Laporan Harian')
	], default='sales')
	
	daily_report = fields.Binary("File Daily Report", help='Recap Daily Report')
	
	def print_daily_report(self, context={}):
		self.ensure_one()
		if self.type == "sales":
			return {
				'type': 'ir.actions.report',
				'report_name':'mgm.daily_report',
				'model':'sale.order',
				'report_type':"qweb-pdf",
			}
		elif self.type == "admin":
			return {
				'type': 'ir.actions.report',
				'report_name':'mgm.daily_report_xlsx',
				'model':'sale.order',
				'report_type':"xlsx",
			}
	
	def upload_daily_report(self):
		if self.daily_report:
			try:
				file_data = base64.b64decode(self.daily_report)
				book = open_workbook(file_contents=file_data)
			except (TypeError, XLRDError) as e:
				raise ValidationError(
					_('It appears that the file you upload is not in valid format, or is corrupted. Details: {}').format(e))
			
			sheet = book.sheets()[0]
			date = datetime.now().strftime('%d%m%y')
			if str(sheet.cell(8, 222).value).upper() != date:
				raise ValidationError(_("The file you uploaded is no longer valid, please re-download template"))
			col_sales = 0
			col_area = 1
			col_customer = 2
			col_report = 3
			col_telp = 4
			col_stamp = 5
			col_sign = 6
			for i in range(sheet.nrows):
				if i == 8:
					if str(sheet.cell(i, col_sales).value).upper() == 'NAMA SALES' and str(sheet.cell(i, col_area).value).upper() == 'AREA' and str(sheet.cell(i, col_customer).value).upper() == 'CUSTOMER' and str(sheet.cell(i, col_report).value).upper() == 'ISI LAPORAN HARIAN' and str(sheet.cell(i, col_telp).value).upper() == 'NO.TELP' and str(sheet.cell(i, col_stamp).value).upper() == 'STEMPEL' and str(sheet.cell(i, col_sign).value).upper() == 'TTD':
						continue
					else:
						raise ValidationError(_("Document does not match.\n Please enter the document containing:\n- Nama Sales\n- Area\n- Customer\n- Isi Laporan Harian\n- No.Telp\n- Stempel\n- Ttd"))
					
				elif i > 8:
					sales = sheet.cell(i, col_sales).value
					area = sheet.cell(i, col_area).value
					customer = sheet.cell(i, col_customer).value
					report = sheet.cell(i, col_report).value
					telp = str(int(sheet.cell(i, col_telp).value))
					if str(sheet.cell(i, col_stamp).value).upper() == 'ADA':
						stamp = "true"
					elif str(sheet.cell(i, col_stamp).value).upper() == 'TIDAK ADA':
						stamp = "false"
					else:
						raise ValidationError(_("Incorrect data entry format, follow the data entry instructions listed on the template: Stempel"))
					if str(sheet.cell(i, col_sign).value).upper() == 'ADA':
						sign = "true"
					elif str(sheet.cell(i, col_sign).value).upper() == 'TIDAK ADA':
						sign = "false"
					else:
						raise ValidationError(_("Incorrect data entry format, follow the data entry instructions listed on the template: Ttd"))
					self._cr.execute("""
                        SELECT id FROM daily_report
                        WHERE (input_date = '%s' and name = '%s' and customer = '%s')
                        """ % (
						date,
						sales,
						customer
					))
					
					daily_report_id = self._cr.dictfetchall()
					if daily_report_id:
						self._cr.execute("""
							UPDATE daily_report
							SET date = '%s',
								input_date = '%s',
								name = '%s',
								area = '%s',
								customer = '%s',
								report = '%s',
								phone = '%s',
								stamp = '%s',
								sign = '%s'
							WHERE id = '%s'
						""" % (
							datetime.now(),
							date,
							sales,
							area,
							customer,
							report,
							telp,
							stamp,
							sign,
							daily_report_id[0]['id']
						))
					else:
						self._cr.execute("""
							INSERT INTO daily_report(date, input_date, name, area, customer, report, phone, stamp, sign)
							VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');
						""" % (
							datetime.now(),
							date,
							sales,
							area,
							customer,
							report,
							telp,
							stamp,
							sign
						))
			return {
				'name': _('Daily Report'),
				'type': 'ir.actions.act_window',
				'view_mode': 'tree,form',
				'res_model': 'daily.report',
				'target': 'current'
			}