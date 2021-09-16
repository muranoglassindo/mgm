from datetime import datetime
from odoo import models


class DailyReportXlsx(models.AbstractModel):
	_name = 'report.mgm.daily_report_xlsx'
	_inherit = 'report.odoo_report_xlsx.abstract'
	
	def generate_xlsx_report(self, workbook, data, lines):
		# Membuat template rekapitulasi laporan harian
		for obj in lines:
			date = datetime.now().strftime('%d%m%y')
			format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True, 'fg_color': 'yellow', 'border': 1})
			format2 = workbook.add_format({
				'bold': 1,
				'border': 1,
				'align': 'left',
				'valign': 'vcenter',
				'text_wrap': True,
				'color': 'red'})
			format3 = workbook.add_format({
				'bold': 1,
				'border': 1,
				'align': 'center',
				'valign': 'vcenter',
				'fg_color': 'red',
			})
			head = workbook.add_format({
				'font_size': 14,
				'border': 1,
				'bold': True,
				'valign': 'vcenter',
				'align': 'center',
			})
			sheet = workbook.add_worksheet('Daily Report')
			format4 = workbook.add_format({'color': 'white'})
			sheet.set_column('A:G',15)
			sheet.merge_range('A1:G2', 'FORM', head)
			sheet.merge_range('A3:G5', 'REKAPITULASI LAPORAN HARIAN', head)
			sheet.write(8, 0, 'Nama Sales', format1)
			sheet.write(8, 1, 'Area', format1)
			sheet.write(8, 2, 'Customer', format1)
			sheet.write(8, 3, 'Isi Laporan Harian', format1)
			sheet.write(8, 4, 'No.Telp', format1)
			sheet.write(8, 5, 'Stempel', format1)
			sheet.write(8, 6, 'Ttd', format1)
			sheet.write(8, 222, date, format4)
			sheet.merge_range('K1:T1', 'PETUNJUK PENGISIAN DATA', format1)
			sheet.merge_range('K2:T9', '1. Nama Sales diisi nama sales,\n2. Area diisi oleh Area Sales\n3. Customer diisi oleh nama customer\n4. Isi Laporan Harian diisi sesuai dengan pengisian laposan harian sales\n5. Nomor Telepon diisi dengan nomor telepon yang disesuaikan dengan data laporan harian sales\n6. Stempel diisi pilihan ada atau tidak ada disesuaikan dengan data laporan harian sales\n7. Ttd diisi pilihan ada atau tidak ada disesuaikan dengan data laporan harian sales', format2)
			# sheet.merge_range('K12:T13', 'DILARANG MERUBAH TEMPLATE INI!', format3)