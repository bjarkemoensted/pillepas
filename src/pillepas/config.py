import pathlib
import yaml

_here = pathlib.Path(__file__).parent.resolve()
form_fields_file = _here / 'form_fields.yaml'


with open(form_fields_file) as f:
    fields = yaml.safe_load(f)


url = "https://www.apoteket.dk/pillepas"

appname = "pillepas"

config_env_var = 'PILLEPAS_CONFIG_DIR'
config_data_filename = 'data.json'

date_format = r"%d-%m-%Y"  # dd-mm-yyy because of reasons


if __name__ == '__main__':
    print(fields)