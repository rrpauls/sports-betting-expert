import xml.etree.ElementTree as ET
from scripts.schedulers import task_xml
print(task_xml(['python', 'test.py'], 'S-1-5-21-123').decode('utf-16'))
