#!/usr/bin/env python3
"""Test environment variable loading"""
import os
from dotenv import load_dotenv

# Load .env file explicitly
env_path = '/mnt/c/Users/avibm/Agentic-Studio-Voice/backend/.env'
print(f"Loading environment from: {env_path}")

load_dotenv(env_path)

print("Environment variables after loading:")
print(f"TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT_FOUND')}")
print(f"TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN', 'NOT_FOUND')[:10]}...")
print(f"FIREBASE_SERVICE_ACCOUNT_KEY present: {bool(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))}")