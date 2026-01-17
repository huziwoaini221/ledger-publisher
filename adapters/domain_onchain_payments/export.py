"""
Example adapter for domain-onchain-payments profile.

Exports data from internal systems to records format.
"""

import json
from datetime import datetime
from typing import List, Dict, Any


def export_from_csv(csv_file: str, output_file: str) -> None:
    """
    Export records from CSV to JSONL format.

    Expected CSV columns (headers):
    domain, chain, txid, timestamp, currency, amount, from, to, token_contract, decimals, purpose, order_id, memo

    Args:
        csv_file: Input CSV file path
        output_file: Output JSONL file path
    """
    import csv

    records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row or not any(row.values()):
                continue

            # Convert to record format
            record = {
                "domain": row["domain"],
                "chain": row["chain"],
                "txid": row["txid"],
                "timestamp": row["timestamp"],
                "currency": row["currency"],
                "amount": row["amount"]
            }

            # Optional fields
            if "from" in row and row["from"]:
                record["from"] = row["from"]
            if "to" in row and row["to"]:
                record["to"] = row["to"]
            if "token_contract" in row and row["token_contract"]:
                record["token_contract"] = row["token_contract"]
            if "decimals" in row and row["decimals"]:
                record["decimals"] = row["decimals"]
            if "purpose" in row and row["purpose"]:
                record["purpose"] = row["purpose"]
            if "order_id" in row and row["order_id"]:
                record["order_id"] = row["order_id"]
            if "memo" in row and row["memo"]:
                record["memo"] = row["memo"]

            records.append(record)

    # Write to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')

    print(f"✅ Exported {len(records)} records to {output_file}")


def generate_sample_records(output_file: str, count: int = 100) -> None:
    """
    Generate sample records for testing.

    Args:
        output_file: Output JSONL file path
        count: Number of records to generate
    """
    import random

    chains = ["ethereum", "base", "arbitrum", "polygon", "optimism"]
    domains = ["example.com", "test.org", "demo.net", "sample.io"]
    purposes = ["payment", "refund", "deposit", "withdrawal"]

    records = []
    for i in range(count):
        record = {
            "domain": random.choice(domains),
            "chain": random.choice(chains),
            "txid": f"0x{''.join(random.choice('0123456789abcdef') for _ in range(64))}",
            "timestamp": datetime.now().isoformat() + "Z",
            "currency": "USD",
            "amount": f"{random.uniform(1, 1000):.2f}",
            "from": f"0x{''.join(random.choice('0123456789abcdef') for _ in range(40))}",
            "to": f"0x{''.join(random.choice('0123456789abcdef') for _ in range(40))}",
            "purpose": random.choice(purposes),
            "order_id": f"ORDER-{datetime.now().strftime('%Y%m%d')}-{i:04d}"
        }
        records.append(record)

    # Write to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')

    print(f"✅ Generated {count} sample records to {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Adapter for domain-onchain-payments")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Export from CSV
    export_parser = subparsers.add_parser("export", help="Export from CSV")
    export_parser.add_argument("--csv", required=True, help="Input CSV file")
    export_parser.add_argument("--output", required=True, help="Output JSONL file")

    # Generate samples
    sample_parser = subparsers.add_parser("sample", help="Generate sample records")
    sample_parser.add_argument("--output", required=True, help="Output JSONL file")
    sample_parser.add_argument("--count", type=int, default=100, help="Number of records")

    args = parser.parse_args()

    if args.command == "export":
        export_from_csv(args.csv, args.output)
    elif args.command == "sample":
        generate_sample_records(args.output, args.count)
