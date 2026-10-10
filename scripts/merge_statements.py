#!/usr/bin/env python3
"""
Merge and sanitize bank statement CSV files from data/raw_csv into clean, parsable CSVs.

Supports:
- Debit statements (ADCB current/savings accounts) -> data/debit_statement_merged.csv
- Credit statements (ADCB credit cards) -> data/credit_statement_merged.csv
"""

import os
import csv
import re
from datetime import datetime
from pathlib import Path


def parse_date(date_str):
    """Parses DD/MM/YYYY into a datetime object for sorting."""
    return datetime.strptime(date_str, "%d/%m/%Y")


def parse_raw_debit_statement(file_path):
    """
    Parses a single raw debit statement CSV file.
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    metadata = {}
    header_idx = -1
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if "Posting Date" in line:
            header_idx = idx
            break
        m = re.match(r'^"?([^:]+):\s*(.*?)"?\s*,?$', line_clean)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            metadata[key] = val

    if header_idx == -1:
        raise ValueError(f"Could not find 'Posting Date' table header in {file_path}")

    reader = csv.reader(lines[header_idx:])
    header = [h.strip() for h in next(reader)]

    cleaned_rows = []
    for row in reader:
        if not row or not any(row):
            continue
        if len(row) != len(header):
            raise ValueError(f"Row length mismatch in {file_path}: expected {len(header)}, got {len(row)}: {row}")

        cleaned_row = [" ".join(col.split()).strip() for col in row]
        cleaned_rows.append(cleaned_row)

    return metadata, header, cleaned_rows


def merge_debit_statements(input_dir, output_file):
    input_path = Path(input_dir)
    csv_files = sorted(input_path.glob("debit_statement*.csv"))

    if not csv_files:
        print(f"No debit CSV files found in {input_dir}")
        return

    all_statements = []
    master_header = None

    for csv_file in csv_files:
        metadata, header, rows = parse_raw_debit_statement(csv_file)
        if master_header is None:
            master_header = header
        elif master_header != header:
            raise ValueError(f"Header mismatch in {csv_file.name}: {header} vs {master_header}")

        first_tx_date = parse_date(rows[0][0])
        last_tx_date = parse_date(rows[-1][0])

        all_statements.append({
            "file": csv_file.name,
            "metadata": metadata,
            "rows": rows,
            "newest_date": max(first_tx_date, last_tx_date),
            "oldest_date": min(first_tx_date, last_tx_date),
        })

    all_statements.sort(key=lambda s: s["newest_date"], reverse=True)

    merged_rows = []
    for stmt in all_statements:
        merged_rows.extend(stmt["rows"])

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(master_header)
        writer.writerows(merged_rows)

    total_debits = sum(float(r[4].replace(",", "")) for r in merged_rows if r[4])
    total_credits = sum(float(r[5].replace(",", "")) for r in merged_rows if r[5])
    opening_bal = float(merged_rows[-1][6].replace(",", "")) + float(merged_rows[-1][4].replace(",", "")) - float(merged_rows[-1][5].replace(",", ""))
    closing_bal = float(merged_rows[0][6].replace(",", ""))

    print(f"--- DEBIT STATEMENTS MERGED ---")
    print(f"Destination: {output_file}")
    print(f"Files merged: {len(csv_files)} ({', '.join(f.name for f in csv_files)})")
    print(f"Total Transactions: {len(merged_rows)}")
    print(f"Date Range: {merged_rows[-1][0]} to {merged_rows[0][0]}")
    print(f"Total Debits:  {total_debits:,.2f} AED")
    print(f"Total Credits: {total_credits:,.2f} AED")
    print(f"Net Change:    {total_credits - total_debits:,.2f} AED")
    print(f"Opening Balance: {opening_bal:,.2f} AED")
    print(f"Closing Balance: {closing_bal:,.2f} AED")
    expected_closing = round(opening_bal - total_debits + total_credits, 2)
    assert abs(expected_closing - round(closing_bal, 2)) < 0.01
    print("Balance Verification: PASSED (Exact Match)\n")


def parse_raw_credit_statement(file_path):
    """
    Parses a single raw credit statement CSV file.
    Extracts statement metadata, skips the subheader card info row, and normalizes rows.
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    metadata = {}
    header_idx = -1
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if "Transaction Date" in line:
            header_idx = idx
            break
        m = re.match(r'^"?([^:]+):\s*(.*?)"?\s*,?$', line_clean)
        if m:
            key, val = m.group(1).strip(), m.group(2).strip()
            metadata[key] = val

    if header_idx == -1:
        raise ValueError(f"Could not find 'Transaction Date' header in {file_path}")

    # Read the table header
    header_line = lines[header_idx]
    header_reader = csv.reader([header_line])
    header = [h.strip() for h in next(header_reader)]

    # Next line is card info (e.g. Primary Card Number:..., Card Holder Name:...)
    card_info_line = lines[header_idx + 1] if len(lines) > header_idx + 1 else ""
    metadata["Card Info"] = card_info_line.strip()

    # Transaction rows start at header_idx + 2
    reader = csv.reader(lines[header_idx + 2:])
    cleaned_rows = []
    for row in reader:
        if not row or not any(row):
            continue
        if len(row) != len(header):
            raise ValueError(f"Row length mismatch in {file_path}: expected {len(header)}, got {len(row)}: {row}")

        cleaned_row = [" ".join(col.split()).strip() for col in row]
        cleaned_rows.append(cleaned_row)

    return metadata, header, cleaned_rows


def merge_credit_statements(input_dir, output_file):
    input_path = Path(input_dir)
    csv_files = sorted(input_path.glob("credit_statement_*.csv"))

    if not csv_files:
        print(f"No credit CSV files found in {input_dir}")
        return

    all_statements = []
    master_header = None

    for csv_file in csv_files:
        metadata, header, rows = parse_raw_credit_statement(csv_file)
        if master_header is None:
            master_header = header
        elif master_header != header:
            raise ValueError(f"Header mismatch in {csv_file.name}: {header} vs {master_header}")

        if not rows:
            continue

        first_tx_date = parse_date(rows[0][0])
        last_tx_date = parse_date(rows[-1][0])

        all_statements.append({
            "file": csv_file.name,
            "metadata": metadata,
            "rows": rows,
            "newest_date": max(first_tx_date, last_tx_date),
            "oldest_date": min(first_tx_date, last_tx_date),
        })

    # Sort statements reverse-chronologically (newest statement first)
    all_statements.sort(key=lambda s: s["newest_date"], reverse=True)

    merged_rows = []
    for stmt in all_statements:
        merged_rows.extend(stmt["rows"])

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(master_header)
        writer.writerows(merged_rows)

    total_dr = sum(float(r[3].replace(",", "")) for r in merged_rows if r[2] == "DR")
    total_cr = sum(float(r[3].replace(",", "")) for r in merged_rows if r[2] == "CR")
    dr_count = sum(1 for r in merged_rows if r[2] == "DR")
    cr_count = sum(1 for r in merged_rows if r[2] == "CR")

    print(f"--- CREDIT STATEMENTS MERGED ---")
    print(f"Destination: {output_file}")
    print(f"Files merged: {len(csv_files)} ({', '.join(f.name for f in csv_files)})")
    print(f"Total Transactions: {len(merged_rows)}")
    print(f"Date Range: {merged_rows[-1][0]} to {merged_rows[0][0]}")
    print(f"Total Debits (DR):  {total_dr:,.2f} AED ({dr_count} transactions)")
    print(f"Total Credits (CR): {total_cr:,.2f} AED ({cr_count} transactions)")
    print(f"Net Spend (DR - CR): {total_dr - total_cr:,.2f} AED")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    raw_csv_dir = repo_root / "data" / "raw_csv"

    debit_output_csv = repo_root / "data" / "debit_statement_merged.csv"
    credit_output_csv = repo_root / "data" / "credit_statement_merged.csv"

    merge_debit_statements(raw_csv_dir, debit_output_csv)
    merge_credit_statements(raw_csv_dir, credit_output_csv)
