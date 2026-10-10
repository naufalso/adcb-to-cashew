#!/usr/bin/env python3
"""
Convert bank statements (credit and debit) into Cashew import CSV format.
Adheres strictly to the Cashew template: Date,Amount,Category,Title,Note,Account
Reference: https://cashewapp.web.app/faq.html
"""

import os
import csv
import re
import argparse
from datetime import datetime
from pathlib import Path


def parse_date_to_cashew(date_str, time_str="12:00:00.000"):
    """
    Converts DD/MM/YYYY into YYYY-MM-DD HH:MM:SS.000
    """
    dt = datetime.strptime(date_str.strip(), "%d/%m/%Y")
    return f"{dt.strftime('%Y-%m-%d')} {time_str}"


def clean_title(desc):
    """
    Cleans raw transaction descriptions into clear, human-friendly titles.
    """
    d = desc.strip()

    # ATM Withdrawal
    if d.startswith("ATM WDL"):
        m = re.search(r"ATM WDL\s+(?:\d{1,2}:\d{2}\s+)?(.*)", d)
        if m:
            clean_loc = re.sub(r"\s+\d{6,}$", "", m.group(1).strip())
            return f"ATM Withdrawal ({clean_loc.title()})"
        return "ATM Withdrawal"

    # Mobile / Bank Transfer Out
    if "MBTRF" in d and "TRF OUT TO" in d:
        m = re.search(r"TRF OUT TO\s+(.*)", d)
        if m:
            name = m.group(1).strip().title()
            return f"Transfer to {name}"
        return "Bank Transfer"

    # Transfer In (B/O)
    if "B/O" in d:
        m = re.search(r"B/O\s+(.*)", d)
        if m:
            party = m.group(1).strip()
            party = re.sub(r"\s+PYP\s+NBAD.*", "", party, flags=re.I)
            party = re.sub(r"\s+NBAD.*", "", party, flags=re.I)
            party = re.sub(r"\s+AED\d+.*", "", party, flags=re.I)
            return f"Transfer from {party.strip().title()}"
        return "Inward Transfer"

    # Credit Card payment
    if "CREDIT CARD PAYMNT" in d or "PAYMENT RECEIVED" in d:
        m_card = re.search(r"(\d{4})$", d.strip())
        if m_card:
            return f"Credit Card Payment (Card {m_card.group(1)})"
        return "Credit Card Payment"

    # Salary
    if d.upper() == "SALARY":
        return "Salary"

    # Reversal of duplicated salary
    if "REVERSAL OF DUPLICATED SALARY" in d.upper():
        return "Salary Duplicate Reversal"

    # Cheque clearing
    if "CLEARING CHEQUE" in d.upper():
        return "Clearing Cheque"

    # Remitly
    if "RMTLY*" in d.upper():
        return "Remitly Remittance"

    # Strip PUR prefix
    if d.startswith("PUR "):
        m = re.search(r"PUR\s+\d{2}/\d{2}\s+(.*)", d)
        if m:
            d = m.group(1).strip()
        d = re.sub(r"\s+\d{4}$", "", d)  # card suffix like 6953

    # Remove foreign currency patterns e.g. " - 11.23 EUR" or "33.0 BRL"
    d = re.sub(r"\s*-\s*\d+(?:\.\d+)?\s*[A-Z]{3}", "", d)
    d = re.sub(r"^\d+(?:\.\d+)?\s*[A-Z]{3}\s*", "", d)

    # Remove trailing country/city markers
    d = re.sub(r"\s+ABU\s*DHABI\s+ARE$", "", d, flags=re.I)
    d = re.sub(r"\s+ABUDHABI\s+ARE$", "", d, flags=re.I)
    d = re.sub(r"\s+DUBAI\s+ARE$", "", d, flags=re.I)
    d = re.sub(r"\s+ELECTRA\s+STREE\s+ARE$", "", d, flags=re.I)
    d = re.sub(r"\s+ARE$", "", d, flags=re.I)
    d = re.sub(r"\s+USA$", "", d, flags=re.I)
    d = re.sub(r"\s+NLD$", "", d, flags=re.I)
    d = re.sub(r"\s+IRL.*$", "", d, flags=re.I)
    d = re.sub(r"\s+IDN.*$", "", d, flags=re.I)
    d = re.sub(r"\s+LUX.*$", "", d, flags=re.I)
    d = re.sub(r"\s+Abu\s*Dhabi.*$", "", d, flags=re.I)
    d = re.sub(r"\s+Dubai.*$", "", d, flags=re.I)

    # Specific common merchant cleanup
    d = re.sub(r"\s+LLC(?:\s+SPC|\s+BR|\s+OPC)?$", "", d, flags=re.I)
    d = re.sub(r"\s+SOLE\s+P(?:ROP)?(?:\s+LLC)?$", "", d, flags=re.I)
    d = re.sub(r"\s+BR\s+O(?:F)?.*$", "", d, flags=re.I)

    # Known merchant normalization
    d_up = d.upper()
    if "GOOGLE" in d_up and "ONE" in d_up:
        return "Google One"
    if "ETISALAT" in d_up and "RECHARGE" in d_up:
        return "Etisalat Wasel Recharge"
    if "E& DIGITAL" in d_up:
        return "e& (Etisalat)"
    if "NOON E COMMERCE" in d_up:
        return "Noon E-Commerce"
    if "DAMAN" in d_up:
        return "Daman Insurance Refund"
    if "HOUSEOFTEA" in d_up:
        return "House of Tea"
    if "KABAYAN CU" in d_up:
        return "Kabayan Cuisine"
    if "KWIK N FRE" in d_up:
        return "Kwik N Fresh"
    if "WARUNK SOTO NIKMAT" in d_up:
        return "Warunk Soto Nikmat"
    if "GSI SUPERMALL" in d_up:
        return "GSI Supermall Surabaya"
    if "GOURMET.INTERNATIONAL" in d_up:
        return "Gourmet International"
    if "LULU HYPERMARKET- WTC" in d_up:
        return "Lulu Hypermarket (WTC)"
    if "LULU HYPERMARKET WAHDA" in d_up:
        return "Lulu Hypermarket (Al Wahda)"
    if "EMIRATES LEIS AL WAHDA" in d_up:
        return "Emirates Leisure (Al Wahda)"
    if "ALBAIK" in d_up:
        return "Albaik"
    if "BAIT AL SH" in d_up:
        return "Bait Al Shay"
    if "TEA TIME" in d_up:
        return "Tea Time Cafe"
    if "CHOWKING" in d_up:
        return "Chowking"
    if "MOMOCHA" in d_up:
        return "Momocha Restaurant"
    if "TANOOR" in d_up:
        return "Al Tanoor Bakery"
    if "YALLA FOOD" in d_up:
        return "Yalla Food"
    if "CRAZY CORN" in d_up:
        return "Crazy Corn"
    if "MALIK AL E" in d_up:
        return "Malik Al Esh"
    if "SHAAZ MART" in d_up:
        return "Shaaz Mart"
    if "AL MOHASSA" in d_up:
        return "Al Mohassal Grocery"
    if "RIVOLI GRO" in d_up:
        return "Rivoli Grocery"
    if "AL IBRAHIM" in d_up:
        return "Al Ibrahim Grocery"
    if "AL MUSHRIF" in d_up:
        return "Al Mushrif Grocery"
    if "AL KHAIZUR" in d_up:
        return "Al Khaizuran Grocery"
    if "ABU TALIB" in d_up:
        return "Abu Talib Cafeteria"
    if "CDM-CASH DEPOSIT" in d_up:
        return "Cash Deposit"
    if "ADNICCLAIMS" in d_up:
        return "ADNIC Insurance Claim"
    if "GCC SWITCH" in d_up:
        return "ATM GCC Switch Fee"
    if "IKEA-AL FU" in d_up:
        return "IKEA (Al Wahda Mall)"
    if "LULUHYPERM" in d_up:
        return "Lulu Hypermarket"

    # Title-case nicely
    words = [w.capitalize() if not (w.isupper() and len(w) <= 3) else w for w in d.split()]
    title = " ".join(words)
    return title.strip() or desc.strip()


def infer_category(desc, is_credit_card, cr_dr, amount, transfer_cards=None):
    """
    Infers one of Cashew's categories:
    - Dining
    - Groceries
    - Shopping
    - Transit
    - Entertainment
    - Bills & Fees
    - Gifts
    - Beauty
    - Work
    - Travel
    - Income
    - others (fallback)
    """
    d_upper = desc.upper()

    # Credit card bill payments & incoming payment received:
    # If the card's statement is imported (in transfer_cards), treat as Transfer to prevent double-counting.
    # Otherwise, treat as Bills & Fees to record spending until statement is available.
    if "PAYMENT RECEIVED" in d_upper:
        return "Transfer"
    if "CREDIT CARD PAYMNT" in d_upper:
        if transfer_cards:
            m_card = re.search(r"(\d{4})$", d_upper.strip())
            if m_card and m_card.group(1) in transfer_cards:
                return "Transfer"
            return "Bills & Fees"
        return "Transfer"

    # Positive inflow / Income
    if cr_dr == "CR" or amount > 0:
        return "Income"

    # Salary duplicate reversal (debit)
    if "REVERSAL OF DUPLICATED SALARY" in d_upper:
        return "Income"

    # Building cleaning services
    if "BLD CLN SRV" in d_upper or "GENERAL CLEANING SER" in d_upper:
        return "Bills & Fees"

    # Personal transfers / Remittance
    if "RMTLY*" in d_upper:
        return "others"
    if "MBTRF" in d_upper:
        return "others"

    # Dining
    dining_keywords = [
        "RESTAURANT", "RESTAURA", "REST", "CAFE", "COFFEE", "BAKERY", "BURGER",
        "CHICBOY", "INASAL", "BIRIYANI", "GRILL", "HOTPOT", "CUISINE", "WOK",
        "MUKBANG", "SHAWARMARY", "HOUSEOFTEA", "TIM HORTONS", "KRISPY KREME",
        "CELADON", "HARU", "ICHIRAM", "WARUNK", "TALABAT", "KEETA", "SMILES FOOD",
        "TABAQ DELI", "TABAQ DELIVERY", "ROYAL CATERING", "ROYAL CATE", "CATERING",
        "FAST FOOD", "HUNGRY POTATO", "IKEA-F&B", "EMIRATES LEIS", "ZIG*",
        "KABAYAN CU", "EMIRATES R ", "ALBAIK", "BAIT AL SH", "TEA TIME", "CHOWKING",
        "MOMOCHA", "TANOOR", "YALLA FOOD", "CRAZY CORN", "MALIK AL E"
    ]
    if any(k in d_upper for k in dining_keywords):
        return "Dining"

    # Groceries
    groceries_keywords = [
        "SUPERMARKET", "HYPERMARKET", "HYPMKT", "GROCERY", "BAQALA", "BUTCHERY",
        "LULU", "VIVA", "BLUE MART", "HOME FRESH", "GRAND EMIRATES", "BESTO",
        "WENCHO", "ORGANIC FOODS", "GOURMET.INTERNATIONAL", "KWIK N FRE",
        "DAY TO DAY", "AL SAFA", "AL NOUKHADA", "AL MUROOJ", "SHAAZ MART",
        "AL MOHASSA", "RIVOLI GRO", "AL IBRAHIM", "AL MUSHRIF", "AL KHAIZUR",
        "BAQALAT", "LULUHYPERM", "ABU TALIB"
    ]
    if any(k in d_upper for k in groceries_keywords):
        return "Groceries"

    # Transit
    transit_keywords = [
        "TAXI", "ADNOC", "TRANSPORT", "YANGO", "METRO", "PARKING", "SALIK",
        "FUEL", "PETROL"
    ]
    if any(k in d_upper for k in transit_keywords):
        return "Transit"

    # Shopping
    shopping_keywords = [
        "ALIEXPRESS", "AMAZON", "NOON", "DAISO", "MUMUSO", "IKEA", "HOME BOX",
        "HOME CENTRE", "LANDMARK", "CROCS", "BRANDS FOR LESS", "FIRSTCRY",
        "STORE", "GSI SUPERMALL", "SLTG SURABAYA", "POWERTEK", "SUPERIOR GENERAL",
        "OTG"
    ]
    if any(k in d_upper for k in shopping_keywords):
        return "Shopping"

    # Bills & Fees / Utilities / Services
    bills_keywords = [
        "POLICE", "TAMM", "ETISALAT", "E& DIGITAL", "INSURANCE", "GOOGLE ONE",
        "GOOGLE*GOOGLE ONE", "TRANSACTION FEE", "VAT ON", "LAUNDRY", "PRETTY STAR",
        "CAR WASH", "CIRRUS", "GCC SWITCH", "SOLUTION TYPING"
    ]
    if any(k in d_upper for k in bills_keywords):
        return "Bills & Fees"

    # Entertainment
    entertainment_keywords = [
        "SPARKYS", "WANASA LAND", "AMUSEMENT", "CINEMA", "VOX", "TIME Z", "TIMEZONE"
    ]
    if any(k in d_upper for k in entertainment_keywords):
        return "Entertainment"

    # Beauty / Health
    beauty_keywords = [
        "HAIRDRESSING", "SALON", "BARBER", "SPA", "IHERB", "MEDICAL", "PHARMACY",
        "CLINIC", "HOSPITAL"
    ]
    if any(k in d_upper for k in beauty_keywords):
        return "Beauty"

    # Travel
    travel_keywords = [
        "GOMOWORLD", "AIRPORT", "FLIGHT", "AIRLINE", "HOTEL", "BOOKING.COM",
        "AGODA", "TECBAN"
    ]
    if any(k in d_upper for k in travel_keywords):
        return "Travel"

    # Work
    work_keywords = [
        "EMIRATES NATIONAL SCHOOL"
    ]
    if any(k in d_upper for k in work_keywords):
        return "Work"

    # Fallback
    return "others"


def process_credit_statement(input_file):
    """
    Parses credit statement CSV (handles raw ADCB statements with preamble lines
    as well as pre-cleaned CSVs) and produces list of Cashew transaction dicts.
    """
    transactions = []
    with open(input_file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    header_idx = -1
    for idx, line in enumerate(lines):
        if "Transaction Date" in line:
            header_idx = idx
            break

    if header_idx == -1:
        raise ValueError(f"Could not find 'Transaction Date' header in {input_file}")

    reader = csv.DictReader(lines[header_idx:])
    for row in reader:
        if not row or not any(row.values()):
            continue
        raw_date = (row.get("Transaction Date") or "").strip()
        # Skip header metadata rows e.g. "Primary Card Number: ..."
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", raw_date):
            continue

        desc = " ".join((row.get("Description") or "").split())
        cr_dr = (row.get("Cr/Dr") or "DR").strip().upper()
        amt_str = (row.get("Amount in AED") or "0").replace(",", "").strip()
        amt_val = float(amt_str) if amt_str else 0.0

        # Cashew format: positive for income, negative for expense
        amount = amt_val if cr_dr == "CR" else -amt_val

        cashew_date = parse_date_to_cashew(raw_date, "12:00:00.000")
        category = infer_category(desc, is_credit_card=True, cr_dr=cr_dr, amount=amount)
        title = clean_title(desc)

        note = desc
        if "EUR" in desc or "BRL" in desc or "IDR" in desc:
            note = f"{desc} | Foreign Currency Transaction"

        transactions.append({
            "Date": cashew_date,
            "Amount": f"{amount:.2f}",
            "Category": category,
            "Title": title,
            "Note": note,
            "Account": "Credit Card",
            "_raw_date": datetime.strptime(raw_date, "%d/%m/%Y"),
        })

    return transactions


def process_debit_statement(input_file, transfer_cards=None):
    """
    Parses debit statement CSV (handles both raw ADCB statements with header metadata
    and pre-cleaned CSVs) and produces list of Cashew transaction dicts.
    """
    transactions = []
    with open(input_file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    header_idx = -1
    for idx, line in enumerate(lines):
        if "Posting Date" in line:
            header_idx = idx
            break

    if header_idx == -1:
        raise ValueError(f"Could not find 'Posting Date' in {input_file}")

    reader = csv.DictReader(lines[header_idx:])
    for row in reader:
        if not row or not any(row.values()):
            continue
        desc = " ".join((row.get("Description") or "").split())
        raw_date = (row.get("Value Date") or "").strip() or (row.get("Posting Date") or "").strip()
        if not raw_date:
            continue

        debit_amt = float(row.get("Debit Amount", "0").replace(",", "") or 0)
        credit_amt = float(row.get("Credit Amount", "0").replace(",", "") or 0)

        if credit_amt > 0:
            amount = credit_amt
            cr_dr = "CR"
        else:
            amount = -debit_amt
            cr_dr = "DR"

        # Check if time exists in description (e.g. ATM WDL 17:22)
        time_str = "12:00:00.000"
        m_time = re.search(r"\b(\d{1,2}):(\d{2})\b", desc)
        if m_time:
            h, m = int(m_time.group(1)), int(m_time.group(2))
            time_str = f"{h:02d}:{m:02d}:00.000"

        cashew_date = parse_date_to_cashew(raw_date, time_str)
        category = infer_category(desc, is_credit_card=False, cr_dr=cr_dr, amount=amount, transfer_cards=transfer_cards)
        title = clean_title(desc)

        ref_no = row.get("Reference No", "").strip()
        note = desc
        if ref_no:
            note = f"{desc} | Ref: {ref_no}"

        transactions.append({
            "Date": cashew_date,
            "Amount": f"{amount:.2f}",
            "Category": category,
            "Title": title,
            "Note": note,
            "Account": "Debit Account",
            "_raw_date": datetime.strptime(raw_date.strip(), "%d/%m/%Y"),
        })

    return transactions


def write_cashew_csv(transactions, output_path):
    """
    Writes transactions to a CSV matching the exact template:
    Date,Amount,Category,Title,Note,Account
    """
    fieldnames = ["Date", "Amount", "Category", "Title", "Note", "Account"]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for t in transactions:
            row = {k: t[k] for k in fieldnames}
            writer.writerow(row)


def detect_imported_cards(data_dir):
    """Detects credit card numbers present in local statement files."""
    cards = set()
    for p in Path(data_dir).glob("**/*credit*.csv"):
        m = re.search(r"(\d{4})", p.name)
        if m:
            cards.add(m.group(1))
    return cards


def main():
    parser = argparse.ArgumentParser(
        description="Convert ADCB bank statements (Credit and Debit) into Cashew CSV import format."
    )
    parser.add_argument(
        "--credit",
        help="Path to credit statement CSV file.",
        default=None,
    )
    parser.add_argument(
        "--debit",
        help="Path to debit statement CSV file.",
        default=None,
    )
    parser.add_argument(
        "--transfer-cards",
        nargs="*",
        help="Last 4 digits of credit cards with imported statements (e.g. 1234) to categorize repayments as Transfer.",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Path to output Cashew CSV file (used when --credit or --debit is explicitly passed).",
        default=None,
    )

    args = parser.parse_args()

    # Custom single/multi file mode
    if args.credit or args.debit:
        all_txs = []
        transfer_cards = set(args.transfer_cards) if args.transfer_cards else None
        if args.credit:
            c_path = Path(args.credit)
            if not c_path.exists():
                raise FileNotFoundError(f"Credit statement file not found: {c_path}")
            all_txs.extend(process_credit_statement(c_path))
        if args.debit:
            d_path = Path(args.debit)
            if not d_path.exists():
                raise FileNotFoundError(f"Debit statement file not found: {d_path}")
            all_txs.extend(process_debit_statement(d_path, transfer_cards=transfer_cards))

        all_txs.sort(key=lambda x: x["_raw_date"], reverse=True)
        out_path = Path(args.output or "cashew_import.csv")
        write_cashew_csv(all_txs, out_path)
        print(f"Exported {len(all_txs)} transactions to {out_path}")
        return

    # Default workspace mode: process standard files in data/
    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / "data"

    credit_files = sorted(data_dir.glob("*credit_statement*.csv"))
    credit_in = credit_files[0] if credit_files else data_dir / "credit_statement_merged.csv"
    debit_in = data_dir / "debit_statement_merged.csv"

    transfer_cards = set(args.transfer_cards) if args.transfer_cards else detect_imported_cards(data_dir)

    credit_txs = process_credit_statement(credit_in) if credit_in.exists() else []
    debit_txs = process_debit_statement(debit_in, transfer_cards=transfer_cards) if debit_in.exists() else []

    print(f"Processed Credit Transactions: {len(credit_txs)}")
    print(f"Processed Debit Transactions:  {len(debit_txs)}")

    credit_txs.sort(key=lambda x: x["_raw_date"], reverse=True)
    debit_txs.sort(key=lambda x: x["_raw_date"], reverse=True)

    all_txs = sorted(credit_txs + debit_txs, key=lambda x: x["_raw_date"], reverse=True)

    if all_txs:
        merged_out = data_dir / "cashew_import_merged.csv"
        write_cashew_csv(all_txs, merged_out)
        print(f"Saved merged import file -> {merged_out} ({len(all_txs)} rows)")

    if credit_txs:
        credit_out = data_dir / "cashew_import_credit.csv"
        write_cashew_csv(credit_txs, credit_out)
        print(f"Saved credit import file -> {credit_out} ({len(credit_txs)} rows)")

    if debit_txs:
        debit_out = data_dir / "cashew_import_debit.csv"
        write_cashew_csv(debit_txs, debit_out)
        print(f"Saved debit import file  -> {debit_out} ({len(debit_txs)} rows)")

    # 2025 Debit Statements
    debit_2025_p1 = data_dir / "raw_csv" / "debit_statement_07-01_2026.csv"
    debit_2025_p2 = data_dir / "raw_csv" / "debit_statement_05-06_2025.csv"
    if debit_2025_p1.exists() and debit_2025_p2.exists():
        txs_2025 = process_debit_statement(debit_2025_p1, transfer_cards=transfer_cards) + process_debit_statement(debit_2025_p2, transfer_cards=transfer_cards)
        txs_2025.sort(key=lambda x: x["_raw_date"], reverse=True)
        debit_2025_out = data_dir / "cashew_import_debit_05_2025-12_2025.csv"
        write_cashew_csv(txs_2025, debit_2025_out)
        print(f"Saved 2025 debit import file -> {debit_2025_out} ({len(txs_2025)} rows)")

    if all_txs:
        from collections import Counter
        cat_summary = Counter(t["Category"] for t in all_txs)
        print("\n--- Combined Category Distribution (2026) ---")
        for cat, count in sorted(cat_summary.items(), key=lambda x: -x[1]):
            print(f"  {cat:15s}: {count:3d} ({count/len(all_txs)*100:.1f}%)")


if __name__ == "__main__":
    main()
