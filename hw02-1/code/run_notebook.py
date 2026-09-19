# 从头执行 hw02-1.ipynb（重启内核语义）
import nbformat
from nbclient import NotebookClient

nb = nbformat.read('hw02-1.ipynb', as_version=4)
client = NotebookClient(nb, timeout=600, kernel_name='fineco',
                        resources={'metadata': {'path': '.'}})
try:
    client.execute()
    print('执行成功，无错误')
except Exception as e:
    print('执行失败:', type(e).__name__)
    print(str(e)[:3000])

nbformat.write(nb, 'hw02-1.ipynb')

# 统计执行情况
n_code = sum(1 for c in nb.cells if c.cell_type == 'code')
executed = sum(1 for c in nb.cells if c.cell_type == 'code' and c.get('execution_count'))
errors = sum(1 for c in nb.cells if c.cell_type == 'code'
             for o in c.get('outputs', []) if o.get('output_type') == 'error')
print(f'代码单元 {n_code}，已执行 {executed}，错误 {errors}')
