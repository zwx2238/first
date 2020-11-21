import re

with open('../Note.txt',encoding='utf8') as fp1,open('../Note2.txt','w',encoding='utf8') as fp2:
	string =""
	for line in fp1:
		line = line.rstrip()
		line,n = re.subn('\t','',line)
		if line.endswith(' >'):
			line = 'sub_root: '+line[:-2].rstrip()
		string += n*'\t'+line+'\n'
	fp2.write(string)