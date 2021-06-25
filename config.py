import jsonpickle


with open(file='./config.json',  mode='r') as config_file:
    _config = jsonpickle.decode(config_file.read())

LogVerbose = _config['log_verbose']
SalesforceConfig = _config['salesforce']

PB_Collection = {}
for pb_item in _config['salesforce']['pb_collection']:
    key = pb_item['name']
    val = pb_item['version']

    PB_Collection[key] = val
