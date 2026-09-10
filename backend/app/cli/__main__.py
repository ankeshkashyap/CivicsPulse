import argparse
import sys
from app.db.session import SessionLocal
from app.services.auth_service import provision_admin_user


def create_admin_command(args: argparse.Namespace) -> int:
    """Provisions or elevates a user to ADMIN role."""
    email = args.email.strip()
    full_name = args.name.strip() if args.name else None

    if not email or "@" not in email:
        print(f"Error: Invalid email address '{email}'", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        user = provision_admin_user(email=email, db=db, full_name=full_name)
        print(f"[SUCCESS] Admin account provisioned: id={user.id}, email={user.email}, role={user.role.value}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Failed to provision admin: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="CivicPulse CLI management tools",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # create-admin subcommand
    admin_parser = subparsers.add_parser("create-admin", help="Provision an administrator account")
    admin_parser.add_argument("--email", required=True, help="Administrator email address")
    admin_parser.add_argument("--name", required=False, default=None, help="Administrator full name")

    args = parser.parse_args()

    if args.subcommand == "create-admin":
        return create_admin_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
