import re
from urllib.parse import urlparse
import warnings

# The version of this library. Unrelated to PFIF versions.
__version__ = '1.0.0'


class PfifError(Exception):
    pass


### XML parser setup #######################################

try:
    import lxml.etree as ET
    _xml_parser = ET.XMLParser(remove_comments=True)
except ImportError:
    import xml.etree.ElementTree as ET
    _xml_parser = ET.XMLParser()


### PFIF versions ##########################################

class Versions:
    V1_0 = '1.0'
    V1_1 = '1.1'
    V1_2 = '1.2'
    V1_3 = '1.3'
    V1_4 = '1.4'
    ALL_VERSIONS = set([V1_0, V1_1, V1_2, V1_3, V1_4])


def validate_version(version):
    if version not in Versions.ALL_VERSIONS:
        raise PfifError('Invalid PFIF version: %s' % version)
    if version != Versions.V1_4:
        warnings.warn('Although this is a valid PFIF version identifier, it\'s '
                      'an old version of PFIF, and its use isn\'t supported by '
                      'this library.')


### Validators #############################################

class SexValues(object):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    ALL_VALUES = set([MALE, FEMALE, OTHER])


class BooleanValues(object):
    TRUE = 'true'
    FALSE = 'false'
    ALL_VALUES = set([TRUE, FALSE])


class StatusValues(object):
    INFORMATION_SOUGHT = 'information_sought'
    IS_NOTE_AUTHOR = 'is_note_author'
    BELIEVED_ALIVE = 'believed_alive'
    BELIEVED_MISSING = 'believed_missing'
    BELIEVED_DEAD = 'believed_dead'
    ALL_VALUES = set([
        INFORMATION_SOUGHT, IS_NOTE_AUTHOR, BELIEVED_ALIVE, BELIEVED_MISSING,
        BELIEVED_DEAD])


_DOMAIN_LABEL_RE = r'[a-zA-Z]([-a-zA-Z0-9]{0,61}[a-zA-Z0-9])?'
_DOMAIN_NAME_RE = r'(' + _DOMAIN_LABEL_RE + r'\.)*' + _DOMAIN_LABEL_RE + r'\.?'
_RECORD_ID_RE = r'^' + _DOMAIN_NAME_RE + r'/.+$'
_DATE_RE = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$'
_EMAIL_RE = r'^.+@' + _DOMAIN_NAME_RE + r'$'
_PHONE_NUMBER_RE = r'^.*\d.*$'
_DATE_OF_BIRTH_RE = r'^\d{4}(-\d{2}(-\d{2})?)?$'
_AGE_RE = r'^\d+(-\d+)?$'
_COUNTRY_RE = r'^[A-Z]{2}$'

_RECORD_ID_MATCHER = re.compile(_RECORD_ID_RE)
_DATE_MATCHER = re.compile(_DATE_RE)
_EMAIL_MATCHER = re.compile(_EMAIL_RE)
_PHONE_NUMBER_MATCHER = re.compile(_PHONE_NUMBER_RE)
_DATE_OF_BIRTH_MATCHER = re.compile(_DATE_OF_BIRTH_RE)
_AGE_MATCHER = re.compile(_AGE_RE)
_COUNTRY_MATCHER = re.compile(_COUNTRY_RE)


def _validate_anything(value):
    pass

def _validate_required_record_id(value):
    if not (value and _RECORD_ID_MATCHER.match(value)):
        raise PfifError('Invalid record ID: %s' % value)

def _validate_optional_record_id(value):
    if value is not None:
        _validate_required_record_id(value)

def _validate_required_date(value):
    if not (value and _DATE_MATCHER.match(value)):
        raise PfifError('Invalid date: %s' % value)

def _validate_optional_date(value):
    if value is not None:
        _validate_required_date(value)

def _validate_optional_email(value):
    if (value is not None) and (not _EMAIL_MATCHER.match(value)):
        raise PfifError('Invalid email: %s' % value)

def _validate_optional_phone(value):
    if (value is not None) and (not _PHONE_NUMBER_MATCHER.match(value)):
        raise PfifError('Invalid phone number: %s' % value)

def _validate_optional_url(value):
    if value is None:
        return
    try:
        parse = urlparse(value)
    except ValueError as e:
        raise PfifError('Invalid URL: %s' % value)
    if not parse.netloc:
        raise PfifError('Invalid URL: %s' % value)

def _validate_optional_urls(value):
    for value_line in value.split('\n'):
        _validate_optional_url(value_line)

def _validate_sex(value):
    if (value is not None) and (value not in SexValues.ALL_VALUES):
        raise PfifError('Invalid sex value: %s' % value)

def _validate_date_of_birth(value):
    if (value is not None) and (not _DATE_OF_BIRTH_MATCHER.match(value)):
        raise PfifError('Invalid date of birth: %s' % value)

def _validate_age(value):
    if (value is not None) and (not _AGE_MATCHER.match(value)):
        raise PfifError('Invalid age: %s' % value)

def _validate_country(value):
    if (value is not None) and (not _COUNTRY_MATCHER.match(value)):
        raise PfifError('Invalid country: %s' % value)

def _validate_optional_boolean(value):
    if (value is not None) and (value not in BooleanValues.ALL_VALUES):
        raise PfifError('Invalid boolean value: %s' % value)

def _validate_status(value):
    if (value is not None) and (value not in StatusValues.ALL_VALUES):
        raise PfifError('Invalid status value: %s' % value)

def _required_text_validator(label):
    def func(value):
        if not value:
            raise PfifError('Empty value for %s' % label)
    return func


_PERSON_FIELD_VALIDATORS = {
    Versions.V1_4: {
        'person_record_id': _validate_required_record_id,
        'entry_date': _validate_optional_date,
        'expiry_date': _validate_optional_date,
        'author_name': _validate_anything,
        'author_email': _validate_optional_email,
        'author_phone': _validate_optional_phone,
        'source_name': _validate_anything,
        'source_date': _validate_required_date,
        'source_url': _validate_optional_url,
        'full_name': _required_text_validator('full name'),
        'given_name': _validate_anything,
        'family_name': _validate_anything,
        'alternate_names': _validate_anything,
        'description': _validate_anything,
        'sex': _validate_sex,
        'date_of_birth': _validate_date_of_birth,
        'age': _validate_age,
        'home_street': _validate_anything,
        'home_neighborhood': _validate_anything,
        'home_city': _validate_anything,
        'home_state': _validate_anything,
        'home_postal_code': _validate_anything,
        'home_country': _validate_country,
        'photo_url': _validate_optional_url,
        'profile_urls': _validate_optional_urls,
    },
}

_NOTE_FIELD_VALIDATORS = {
    Versions.V1_4: {
        'note_record_id': _validate_required_record_id,
        'person_record_id': _validate_required_record_id,
        'linked_person_record_id': _validate_optional_record_id,
        'entry_date': _validate_optional_date,
        'author_name': _required_text_validator('author name'),
        'author_email': _validate_optional_email,
        'author_phone': _validate_optional_phone,
        'source_date': _validate_required_date,
        'author_made_contact': _validate_optional_boolean,
        'status': _validate_status,
        'email_of_found_person': _validate_optional_email,
        'phone_of_found_person': _validate_optional_phone,
        'last_known_location': _validate_anything,
        'text': _required_text_validator('text'),
        'photo_url': _validate_optional_url,
    },
}

def person_field_validators(version):
    return _PERSON_FIELD_VALIDATORS[version]

def note_field_validators(version):
    return _NOTE_FIELD_VALIDATORS[version]


### PFIF documents #########################################

class PfifDocument(object):

    def __init__(self, version, validate=True):
        validate_version(version)
        if version != Versions.V1_4:
            raise NotImplementedError(
                'This library doesn\'t support PFIF versions below 1.4.')
        self._version = version
        self._validate = validate
        if validate:
            self._person_field_validators = person_field_validators(version)
            self._note_field_validators = note_field_validators(version)
        self._persons = []
        self._notes = []

    def add_person(self, **fields):
        if self._validate:
            self._validate_person_fields(fields)
        self._persons.append(fields)

    def add_note(self, **fields):
        if self._validate:
            self._validate_note_fields(fields)
        self._notes.append(fields)

    def _validate_person_fields(self, fields):
        for field_name, value in fields.items():
            if field_name == 'note':
                self._validate_note_fields(value)
            else:
                self._person_field_validators[field_name](value)

    def _validate_note_fields(self, fields):
        for field_name, value in fields.items():
            self._note_field_validators[field_name](value)


### XML parsing ############################################

_TAG_MATCHER = re.compile(r'^\{(http://zesty\.ca/pfif/(.+))\}(.+)$')

def parse(input, validate=True):
    root = ET.parse(input, _xml_parser).getroot()
    root_tag_match = _TAG_MATCHER.match(root.tag)
    if not root_tag_match:
        raise PfifError('Invalid root tag: %s' % root.tag)
    version_str = root_tag_match.group(2)
    validate_version(version_str)
    namespace = root_tag_match.group(1)
    doc = PfifDocument(version_str, validate)
    for person in root.iterfind('{%s}person' % namespace):
        fields = {}
        for child in list(person):
            tag_match = _TAG_MATCHER.match(child.tag)
            if not tag_match:
                raise PfifError('Invalid tag: %s' % child.tag)
            tag = tag_match.group(3)
            if tag == 'note':
                note_fields = {}
                for note_child in list(child):
                    note_tag_match = _TAG_MATCHER.match(note_child.tag)
                    if not note_tag_match:
                        raise PfifError('Invalid tag: %s' % note_child.tag)
                    note_tag = note_tag_match.group(3)
                    if note_child.text:
                        note_fields[note_tag] = note_child.text.strip()
                fields.setdefault('notes', []).append(note_fields)
            else:
                if child.text:
                    fields[tag] = child.text.strip()
        doc.add_person(**fields)
    for note in root.iterfind('{%s}note' % namespace):
        fields = {}
        for child in list(note):
            if child.text:
                tag_match = _TAG_MATCHER.match(child.tag)
                if not tag_match:
                    raise PfifError('Invalid tag: %s' % child.tag)
                tag = tag_match.group(3)
                fields[tag] = child.text.strip()
        doc.add_note(**fields)
