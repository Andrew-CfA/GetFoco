#!/usr/bin/env python
"""
Get FoCo is a platform for application and administration of income-
qualified programs offered by the City of Fort Collins.
Copyright (C) 2019

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    #note you took this out per Asheesh's suggestion during your DevOps testing with implementing environment variables through Azure, check Azure env variables for this below so you don't need to hardcode
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobileVers.settings.production') #.production / .dev put this in to make python manage.py [] easier, don't need to use --settings=...
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
