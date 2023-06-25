#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

    try:
        # external
        from django.core import management
    except ImportError:
        raise ImportError(  # noqa
            "Couldn't import Django. Are you sure it's installed and "
            + 'available on your PYTHONPATH environment variable? Did you '
            + 'forget to activate a virtual environment?',
        )

    management.execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
