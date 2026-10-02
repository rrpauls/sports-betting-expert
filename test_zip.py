import zipfile
from zipfile import ZipFile, ZipInfo

info = ZipInfo('a\\escape')
# info.filename = 'a\\escape' # even without this
with ZipFile('test.zip', 'w') as z:
    z.writestr(info, b'test')

with ZipFile('test.zip', 'r') as z:
    print(z.namelist())
