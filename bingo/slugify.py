
import re

def slugify(value):
	value = re.sub('[^\w\s-]', '', value).strip().lower()
	return re.sub('[-\s]+', '-', value)

