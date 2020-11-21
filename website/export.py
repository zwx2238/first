import pdfkit
import sys
import time

sys.path.insert(0, '..')
from node import *
def export_to_pdfs():
	options={
		'page-size':'A3',
	}
	root=load_txt(ROOT_PATH)
	i=1
	for node in root.all_sub_link_nodes(max_depth=MAX_DEPTH):
		if not node.children:
			continue
		try:
			# 1/0
			query=node.full_path+'+-f'
			file_name='pdf/' + str(i) +' ' + node.sub_root_path + '.pdf'
			config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
			pdfkit.from_url('http://127.0.0.1:5000/search/?q={}'.format(query),file_name,configuration=config,options=options)
			# time.sleep(3)
		except:
			print(node.full_path)
		i+=1

if __name__ == '__main__':
	export_to_pdfs()