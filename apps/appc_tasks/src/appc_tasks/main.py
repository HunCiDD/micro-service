import os

from common.settings import APP_SETTINGS


def main():
    print('Hello from appc-tasks!')


if __name__ == '__main__':
    os.environ.setdefault('APP_NAME', 'appc_tasks')
    settings = APP_SETTINGS
    print(1)
    main()
