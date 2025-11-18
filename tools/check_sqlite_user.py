#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect(r'c:\Users\game1\Desktop\shopKME\db.sqlite3')
cursor = conn.cursor()

# Find user with phone
cursor.execute("SELECT id, phone, password FROM account_user WHERE phone = '0879512117'")
row = cursor.fetchone()

if row:
    print(f"User found in sqlite:")
    print(f"  ID: {row[0]}")
    print(f"  Phone: {row[1]}")
    print(f"  Password hash: {row[2]}")
else:
    print("User not found. All users:")
    cursor.execute("SELECT id, phone FROM account_user")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]}, Phone: {row[1]}")

conn.close()
