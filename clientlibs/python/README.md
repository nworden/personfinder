# PFIF library

For all validators, a value of `None` will pass without raising an exception if
and only if the field is optional. An empty string will pass without raising an
exception for optional free-text fields, but not others (e.g., an empty string
is accepted for the `description` field, but not for the `photo_url` field).

## Dependencies

The library has no hard external dependencies. If the lxml library is available,
the PFIF library will use it, but otherwise it will fall back to the xml module
that ships with Python.

We test on minor Python versions that are less than five years old (currently
Python 3.5, 3.6, and 3.7).

## Development of the library

### Testing

Unit tests can be run with:

```shell
python3 -m unittest test_pfif.py
```
