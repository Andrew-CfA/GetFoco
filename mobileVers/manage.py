#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    #note you took this out per Asheesh's suggestion during your DevOps testing with implementing environment variables through Azure, check Azure env variables for this below so you don't need to hardcode
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobileVers.settings.production') #.production / .debug put this in to make python manage.py [] easier, don't need to use --settings=...
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
