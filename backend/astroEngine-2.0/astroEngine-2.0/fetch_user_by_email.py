import os
import json
import argparse
from db_manager import MongoDBManager

def main():
    parser = argparse.ArgumentParser(description='Fetch horoscope data from MongoDB by email.')
    parser.add_argument('email', type=str, help='Email of the user to fetch data for')
    parser.add_argument('--out', type=str, default='output.json', help='Output JSON file path (default: output.json)')
    args = parser.parse_args()

    # Create manager (will use MONGODB_URI from .env)
    print(f"Connecting to MongoDB...")
    manager = MongoDBManager()
    
    print(f"Fetching data for email: {args.email}")
    data = manager.get_horoscope_by_email(args.email)
    
    if data:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Success! Data for {args.email} saved to {args.out}")
    else:
        print(f"No data found for email: {args.email}")

if __name__ == "__main__":
    main()
