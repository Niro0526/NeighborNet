from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Standardized DRF Exception Handler for NeighborNet AI API.
    Returns consistent { "error": "...", "detail": "...", "status_code": ... }
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'status_code': response.status_code,
            'success': False,
        }

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_data['detail'] = response.data['detail']
            else:
                custom_data['detail'] = 'Validation or processing error'
                custom_data['errors'] = response.data
        elif isinstance(response.data, list):
            custom_data['detail'] = response.data[0] if response.data else 'Error occurred'
            custom_data['errors'] = response.data
        else:
            custom_data['detail'] = str(response.data)

        response.data = custom_data

    return response
