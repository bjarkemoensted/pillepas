# Partition the fields into three categories:
# 'constant', which are assumed rarely change between usages (e.g. name, phone number)
# 'volatile', which change very frequently (e.g. travel start/stop dates and pickup pharmacy)
# 'aggregate', which rarely change but might take multiple values (e.g. different drugs and doses)

fields = {
    'constant': (
        'SubmitModel_FirstName',
        'SubmitModel_LastName',
        'SubmitModel_Address',
        'SubmitModel_PostalCode',
        'SubmitModel_City',
        'SubmitModel_PassportNumber',
        'SubmitModel_BirthDate',
        'SubmitModel_BirthCity',
        'SubmitModel_Country',
        'SubmitModel_Sex1',
        'SubmitModel_Sex2',
        'SubmitModel_PhoneNumber',
        'SubmitModel_Email',
        'SubmitModel_DoctorsFirstName',
        'SubmitModel_DoctorsLastName',
        'SubmitModel_DoctorsAddress',
        'SubmitModel_DoctorsPostalCode',
        'SubmitModel_DoctorsCity',
        'SubmitModel_DoctorsPhone'
    ),
    'volatile': (
        'SubmitModel_TravelStartDate',
        'SubmitModel_TravelEndDate',
        'SubmitModel_PharmacyName'
    ),
    'aggregate': (
        'SubmitModel_SelectedPraeperatName',
        'SubmitModel_DailyDosis',
    )
}


def get_all_ids():
    all_ = []
    for v in fields.values():
        for elem in v:
            all_.append(elem)
        #
    res = tuple(all_)
    return res


# Keep track of which inputs use radio button because clicking those works differently
radio_buttons = ('SubmitModel_Sex1', 'SubmitModel_Sex2')

# ID of the 'decline optional cookies' button
decline_cookies_button_id = "declineButton"