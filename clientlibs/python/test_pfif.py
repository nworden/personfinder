import unittest

import pfif


class FieldValidatorTests(unittest.TestCase):

    def test_required_record_id_validator(self):
        func = pfif._validate_required_record_id
        self.check_validator_passes(func, [
            'www.example.com/abc123',
        ])
        self.check_validator_failures(func, [
            'abc123',
        ])

    def test_date_validator(self):
        optional_func = pfif._validate_optional_date
        self.check_validator_passes(optional_func, [
            '2019-03-29T12:09:00Z',
            '2019-03-29T12:09:05.143Z',
        ])
        self.check_validator_failures(optional_func, [
            '84-02-04T12:09:00Z',
            '2019-03-29T12:09:00',
            '2019-03-29',
        ])
        self.check_validator_failures(pfif._validate_required_date, [None])

    def test_email_validator(self):
        func = pfif._validate_optional_email
        self.check_validator_passes(func, [
            'fred@example.com',
            'a@b',
        ])
        self.check_validator_failures(func, [
            'fred',
            'fred@',
        ])

    def test_date_of_birth_validator(self):
        func = pfif._validate_date_of_birth
        self.check_validator_passes(func, [
            '1991', '1991-02', '1991-02-03', None,
        ])
        self.check_validator_failures(func, [
            '84', '199102', '19910203',
        ])

    def test_age_validator(self):
        func = pfif._validate_age
        self.check_validator_passes(func, [
            '0', '1', '5', '10', '25', '123',
            '0-1', '0-123', '25-30',
            None,
        ])
        self.check_validator_failures(func, [
            '-12', 'potato', '12-abc', 'twenty',
        ])

    def test_status_validator(self):
        func = pfif._validate_status
        self.check_validator_passes(func, [
            'information_sought',
            'is_note_author',
            'believed_alive',
            'believed_missing',
            'believed_dead',
        ])
        self.check_validator_failures(func, [
            'not a valid status',
        ])

    def check_validator_passes(self, func, values):
        for value in values:
            func(value)

    def check_validator_failures(self, func, values):
        for value in values:
             with self.assertRaises(pfif.PfifError, msg=value):
                 func(value)


if __name__ == '__main__':
    unittest.main()
