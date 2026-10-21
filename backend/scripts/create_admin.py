import argparse
import getpass

from backend.app.auth import hash_password
from backend.app.database import connect


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an admin or rotate an existing admin password"
    )
    parser.add_argument("--username", required=True)
    args = parser.parse_args()
    username = args.username.strip().lower()
    if len(username) < 3 or len(username) > 80:
        parser.error("Username must be 3–80 characters")
    password = getpass.getpass("New admin password: ")
    if len(password) < 12:
        parser.error("Password must be at least 12 characters")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("Passwords did not match")
    client, db = connect()
    try:
        db.admin_users.update_one(
            {"username": username},
            {"$set": {"password_hash": hash_password(password)}},
            upsert=True,
        )
        db.admin_sessions.delete_many({"username": username})
        print(f"Admin {username} is ready. Existing sessions were revoked.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
