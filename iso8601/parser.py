import contextlib
import datetime
import re
import pytz

PARSED_CLASSES = (datetime.date, datetime.timedelta, )


try:
    import freezegun
except ImportError:
    pass
else:
    PARSED_CLASSES = PARSED_CLASSES + (freezegun.api.FakeDate, )


INVALID_FLOAT_MESSAGES = [
    'invalid literal for float()',
    'could not convert string to float',
]


FORMATS = [
    '%Y-%m-%dT%H:%M:%S%z',
    '%Y-%m-%dT%H:%M:%S%Z',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%dT%H',
    '%Y-%m-%d',
    '%Y%m%d',
    '%Y%m%dT%H%M%S%z',
    '%Y%m%dT%H%M%S%Z',
    '%Y%m%dT%H%M%S',
]

def parse(data):
    """
    Handle any of the valid ISO 8601 times, and convert to a python
    datetime object.

    >>> parse('2010-01-01')
    datetime.datetime(2010, 1, 1, 0, 0)
    >>> parse('2010-01-01T00:00:00')
    datetime.datetime(2010, 1, 1, 0, 0)
    >>> parse('2010-01-01 00:00:00')
    datetime.datetime(2010, 1, 1, 0, 0)
    >>> parse('2010-01-01 24:00:00')
    datetime.datetime(2010, 1, 2, 0, 0)
    >>> parse('2010-01-01 24:01:00')
    Traceback (most recent call last):
        ...
    ValueError: hour=24 is only permitted at midnight
    >>> parse('2010-01-01T24')
    datetime.datetime(2010, 1, 2, 0, 0)

    >>> parse('2010-01-01T01.5')
    datetime.datetime(2010, 1, 1, 1, 30)
    >>> parse('2010-01-01T01:01.5')
    datetime.datetime(2010, 1, 1, 1, 1, 30)
    >>> parse('2010-01-01T01:01:01.5')
    datetime.datetime(2010, 1, 1, 1, 1, 1, 500000)
    >>> parse('2010-01-01T24.5')
    Traceback (most recent call last):
        ...
    ValueError: hour=24 is only permitted at midnight
    >>> parse('2010-01-01T01.5:00')
    Traceback (most recent call last):
        ...
    ValueError: fractional time may only apply to last component
    >>> parse('2010-01-01T01.5:00.5')
    Traceback (most recent call last):
        ...
    ValueError: fractional time may only apply to last component

    >>> parse('P7D')
    datetime.timedelta(days=7)
    >>> parse('P14D')
    datetime.timedelta(days=14)
    >>> parse('P1DT')
    Traceback (most recent call last):
        ...
    ValueError: 'P1DT' does not match ISO8601 format
    >>> parse('P1D2H')
    Traceback (most recent call last):
        ...
    ValueError: 'P1D2H' does not match ISO8601 format
    >>> parse('P1DT2H')
    datetime.timedelta(days=1, seconds=7200)
    >>> parse('P1Y')
    Traceback (most recent call last):
        ...
    ValueError: Year and month values are not supported in python timedelta

    >>> parse('2012-02-03T09:00:00Z')
    datetime.datetime(2012, 2, 3, 9, 0, tzinfo=datetime.timezone.utc)

    >>> parse('2023-11-28T06:15:00-06:00')
    datetime.datetime(2023, 11, 28, 6, 15, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=64800)))
    """

    if isinstance(data, PARSED_CLASSES):
        return data

    if 'P' in data:
        dt, duration = data.split('P')
        if dt:
            return parse(dt), parse_duration(duration)
        return parse_duration(duration)

    if 'T' not in data:
        data = data.replace(' ', 'T')

    for format in FORMATS:
        with contextlib.suppress(ValueError):
            return datetime.datetime.strptime(data, format)

    date_part, time_part = data.split('T')

    if time_part.startswith('24'):
        result = parse(data.replace('T24', 'T00')) + datetime.timedelta(1)
        if result.minute or result.second or result.microsecond:
            raise ValueError('hour=24 is only permitted at midnight')
        return result

    if time_part.count('.') > 1:
        raise ValueError('fractional time may only apply to last component')
    if time_part.count('.'):
        try:
            fraction = float("0.%s" % time_part.split('.')[1])
        except ValueError as arg:
            message = arg.args[0].split(':')[0]
            if message in INVALID_FLOAT_MESSAGES:
                raise ValueError("fractional time may only apply to last component")
            raise

        if time_part.count(':') == 0:
            fraction = datetime.timedelta(hours=fraction)
        elif time_part.count(':') == 1:
            fraction = datetime.timedelta(minutes=fraction)
        elif time_part.count(':') == 2:
            fraction = datetime.timedelta(seconds=fraction)

        return parse(data.split('.')[0]) + fraction


DATE_REGEX = r'(?P<year>\d{4})-(?P<month>\d\d)-(?P<day>\d\d)'


def parse_date(date):
    """
    >>> parse_date('2012-01-01')
    datetime.date(2012, 1, 1)
    >>> parse_date('2012-02-03T09:00:00')
    datetime.date(2012, 2, 3)
    """
    result = parse(date)
    if hasattr(result, 'date'):
        return result.date()
    return result


def parse_time(time):
    result = parse(time)
    if hasattr(result, 'time'):
        return result.time()
    return result


# TODO Allow least significant to be a float.
duration_regex = re.compile(
    r'^P?'
    r'((?P<years>\d+)Y)?'
    r'((?P<months>\d+)M)?'
    r'((?P<weeks>\d+)W)?'
    r'((?P<days>\d+)D)?'
    r'(T'
    r'((?P<hours>\d+)H)?'
    r'((?P<minutes>\d+)M)?'
    r'((?P<seconds>\d+)S)?'
    r')?$'
)


def duration_parts(duration):
    data = duration_regex.match(duration)
    if not data or duration[-1] == 'T':
        raise ValueError("'P%s' does not match ISO8601 format" % duration)
    return dict([(k, int(v)) for k, v in data.groupdict().items() if v and int(v)])


def parse_duration(duration):
    data = duration_parts(duration)
    if 'years' in data or 'months' in data:
        raise ValueError('Year and month values are not supported in python timedelta')
    return datetime.timedelta(**data)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
