#!/usr/bin/env python3

"""
Script to create MongoDb users for X-Road OpMon tools.
"""

from pymongo import MongoClient
import sys
import argparse
import getpass
import string
import secrets

user_roles = {
    'analyzer': {'query_db': 'read', 'analyzer_database': 'readWrite'},
    'analyzer_interface': {'query_db': 'read', 'analyzer_database': 'readWrite'},
    'anonymizer': {'query_db': 'read', 'anonymizer_state': 'readWrite'},
    'collector': {'query_db': 'readWrite', 'collcetor_state': 'readWrite'},
    'corrector': {'query_db': 'readWrite'},
    'reports': {'query_db': 'read', 'reports_state': 'readWrite'}
}

admin_roles = {
    'root': ['root'],
    'backup': ['backup'],
    'superuser': ['root']
}


def main():
    passwords = {}
    args = _parse_args()
    client = _connect_mongo(args)

    _create_admin_users(args, client, passwords)
    _create_opmon_users(args, client, passwords)
    _print_users(passwords)


def _connect_mongo(args):
    if args.user is None:
        return MongoClient(args.host)
    
    password = args.password or getpass.getpass()
    return MongoClient(
        args.host,
        username=args.user,
        password=password,
        authSource=args.auth
    )


def _create_admin_users(args, client, passwords):
    if not args.generate_admins:
        return

    for user_name, roles in admin_roles.items():
        passwords[user_name] = user_name if args.dummy_passwords else _generate_password()
        client.admin.command('createUser', user_name, pwd=passwords[user_name], roles=roles)


def _create_opmon_users(args, client, passwords):
    for user, roles in user_roles.items():
        user_name = '{}_{}'.format(user, args.xroad)
        role_list = _roles_to_list(roles)
        passwords[user_name] = user_name if args.dummy_passwords else _generate_password()

        client.auth_db.command('createUser', user_name, pwd=passwords[user_name], roles=role_list)


def _roles_to_list(roles):
    return [{'db': db, 'role': role} for db, role in roles.items()]


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("xroad", metavar="X-ROAD-INSTANCE", help="X-Road instance name.")
    parser.add_argument("--host", metavar="HOST:PORT", default="localhost:27017", help="MongoDb host:port. Default is localhost:27017")
    parser.add_argument("--user", help='MongoDb username', default=None)
    parser.add_argument("--password", help='MongoDb password', default=None)
    parser.add_argument('--auth', help='Authorization Database', default='admin')
    parser.add_argument("--dummy-passwords", action="store_true", help="Skip generation of secure passwords for users. Password will be same as username.")
    parser.add_argument("--generate-admins", action="store_true", help="Also generate admin users.")
    args = parser.parse_args()

    return args


def _print_users(passwords):
    width = max([len(k) for k in passwords.keys()]) + 1

    print("\nGenerated following users: \n")
    print(f'{"Username":<{width}}| Password')
    print(f'{width * "-"}+{"-"*20}')
    [print(f'{user:<{width}}| {password}') for user, password in passwords.items()]


def _generate_password():
    """
    Generate a random 12 character password.
    
    Password contains lower-case, upper-case, numbers and special characters.
    Based on best-practice recipe from https://docs.python.org/3/library/secrets.html.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(12))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3
                and any(c in string.punctuation for c in password)):
            return password


if __name__ == '__main__':
    main()