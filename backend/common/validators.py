from django.core.exceptions import ValidationError
import math

def validate_positive_quantity(value):
    if not math.isfinite(value) or value <= 0:
        raise ValidationError('Quantity must be strictly greater than zero.')

def validate_latitude(value):
    if value < -90.0 or value > 90.0:
        raise ValidationError('Latitude must be between -90.0 and 90.0 degrees.')

def validate_longitude(value):
    if value < -180.0 or value > 180.0:
        raise ValidationError('Longitude must be between -180.0 and 180.0 degrees.')
