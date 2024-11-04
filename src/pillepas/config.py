import pathlib
import yaml

_here = pathlib.Path(__file__).parent.resolve()
form_fields_file = _here / 'form_fields.yaml'


with open(form_fields_file) as f:
    fields = yaml.safe_load(f)


field2type = {field: type_ for type_, fields in fields.items() for field in fields}


url = "https://www.apoteket.dk/pillepas"

appname = "pillepas"

config_env_var = 'PILLEPAS_CONFIG_DIR'
config_data_filename = 'data.json'

date_format = r"%d-%m-%Y"  # dd-mm-yyy because of reasons

# Input fields for sensitive data which we should not save by default unless encryption is used
sensitive_fields = ("PassportNumber",)

# Special hidden input field which should not be filled out.
form_id_field = "FormId"

# This maps the input categories where we store multiple values, to the unique id for each
aggregate_field2id = {
    "medicines": "SelectedPraeperat",
    "pharmacies": "PharmacyId"
}

if __name__ == '__main__':
    print(fields)