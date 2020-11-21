import os
from PyPDF2 import PdfFileMerger


def func(file):
    num = int(file.split()[0])
    return num


target_path = 'pdf'
pdf_lst = [f for f in os.listdir(target_path) if f.endswith('.pdf')]
pdf_lst = sorted(pdf_lst, key=func)
pdf_lst = [os.path.join(target_path, filename) for filename in pdf_lst]

file_merger = PdfFileMerger()
for pdf in pdf_lst:
    # print(pdf)
    page = len(file_merger.pages)
    # file_merger.addPage(page)
    print(page)
    file_merger.append(pdf)  # 合并pdf文件
    title = pdf[4:-4]
    _, title = title.split(' ', 1)
    try:
        *l, parent, title = title.split('--')
        # print(l,parent,title)
    except ValueError:
        parent = None
    # parent = None
    print(title, parent)
    file_merger.addBookmark(title, pagenum=page, parent=parent)

file_merger.write("Note.pdf")
print("yes")
