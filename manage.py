#!/usr/bin/env python

import os
import sys


def main() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

    try:
        from django.core import management  # noqa: WPS433
    except ImportError:  # noqa: DAR401
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and " +
            'available on your PYTHONPATH environment variable? Did you ' +
            'forget to activate a virtual environment?',
        )

    management.execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
