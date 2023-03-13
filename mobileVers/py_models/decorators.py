from functools import wraps
from django.http import HttpResponse
from django.shortcuts import redirect, reverse


def set_update_mode(view_func):
    """
    Decorator to set the update mode in the session.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get the success query string parameter
        update_mode = request.GET.get('update_mode')
        if update_mode:
            request.session['update_mode'] = True
            return redirect(request.path)

        # Call the original view function
        response = view_func(request, *args, **kwargs)
        return response

    return wrapper
