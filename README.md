# adcb-to-cashew 💳 ➡️ 📊

An open-source utility to convert and merge **Abu Dhabi Commercial Bank (ADCB)** Debit and Credit Card statements into beautifully formatted, categorized CSV files ready for instant import into the **[Cashew Budget App](https://cashewapp.web.app/)**.

---

## 🌟 Why This Exists

If you bank with ADCB and use Cashew (or similar budgeting apps) to track personal finances, you face several challenges:

1. **Messy Bank Statement Formats**: ADCB statements include non-tabular metadata preambles, reversed chronological ordering, and unescaped multi-line text descriptions that break standard CSV importers.
2. **Missing Categories**: Raw bank statements don't categorize your spending into Dining, Groceries, Transit, Bills, etc.
3. **Double Counting Expenses**: When you buy groceries with your Credit Card (`-150 AED`), and later pay your credit card bill from your Current Account (`-150 AED`), budgeting apps will count your expenses **twice** unless the credit card payment is correctly handled as an internal **`Transfer`**.

**`adcb-to-cashew`** solves all of this automatically with zero third-party dependencies.

---

## ✨ Features

- **🚀 Zero Dependencies**: Runs with standard Python 3.8+ (no `pandas` or `numpy` version conflicts).
- **🧹 Statement Sanitization & Validation**:
  - Automatically identifies header positions and ignores bank metadata banners.
  - Normalizes broken multi-line descriptions into clean single-line records.
  - Verifies running balance math across consecutive statements to guarantee zero data loss.
- **🏷️ Smart UAE Merchant Categorization**:
  - Pre-trained keyword mappings for UAE merchants:
    - **Groceries**: Lulu Hypermarket, Viva, Blue Mart, Home Fresh, Baqala, etc.
    - **Dining**: Restaurants, Cafes, Albaik, Talabat, Keeta, House of Tea, etc.
    - **Transit**: ADNOC fuel stations, Taxis (Aman, Arabia, National, Cars), Yango.
    - **Bills & Fees**: Tamm, Abu Dhabi Police, Etisalat / e& recharges, laundry services.
    - **Shopping**: Daiso, Noon, IKEA, Home Centre, AliExpress, etc.
    - **Income**: Salaries, university allowances, insurance refunds.
    - **Transfer**: Linked credit card settlements.
    - **others**: Peer-to-peer bank transfers (MBTRF), ATM cash withdrawals.
- **🔄 Smart Credit Card Repayment Logic**:
  - Prevents double-counting by matching incoming card payments with outgoing debit payments as **`Transfer`**.
  - Intelligently distinguishes between credit cards with imported itemized statements vs. cards awaiting statements.
- **📱 100% Cashew Template Compliant**: Matches the exact schema (`Date`, `Amount`, `Category`, `Title`, `Note`, `Account`).

---

## 📂 Project Structure

```text
adcb-to-cashew/
├── scripts/
│   ├── convert_to_cashew_csv.py   # Main transformer & categorization pipeline
│   └── merge_statements.py        # Statement merger & running balance verifier
├── examples/                      # Anonymized sample statements for testing
│   ├── sample_raw_debit.csv
│   ├── sample_raw_credit.csv
│   └── sample_cashew_import.csv
├── data/                          # Your personal statements (ignored by git)
│   ├── raw_csv/                   # Put downloaded bank CSVs here
│   └── template/                  # Cashew reference templates
├── .gitignore                     # Comprehensive privacy protection
├── LICENSE                        # MIT License
└── README.md
```

---

## 🚀 Quick Start

### 1. Requirements

- Python 3.8 or higher.
- No `pip install` required!

### 2. Basic Command Line Usage

Convert any individual ADCB debit or credit statement into a Cashew-ready CSV:

```bash
# Convert a single debit statement
python3 scripts/convert_to_cashew_csv.py \
  --debit examples/sample_raw_debit.csv \
  --output my_cashew_debit.csv

# Convert a debit and credit statement together into a merged file
python3 scripts/convert_to_cashew_csv.py \
  --debit examples/sample_raw_debit.csv \
  --credit examples/sample_raw_credit.csv \
  --output my_cashew_merged.csv
```

### 3. Automated Batch Processing

Place your exported ADCB statement CSVs into the `data/raw_csv/` directory:

1. **Merge multiple statements**:
   ```bash
   python3 scripts/merge_statements.py
   ```
   *Merges statements in reverse-chronological order and verifies running balance continuity.*

2. **Generate Cashew Import CSVs**:
   ```bash
   python3 scripts/convert_to_cashew_csv.py
   ```
   Outputs ready-to-import files in `data/`:
   - `cashew_import_merged.csv` (All accounts combined)
   - `cashew_import_credit.csv` (Credit card only)
   - `cashew_import_debit.csv` (Debit account only)

---

## 📲 How to Import Into Cashew

1. Open the [Cashew App](https://cashewapp.web.app/) (Web, iOS, or Android).
2. Go to **More** (`...`) → **Settings & Customization** → **Import & Export Data**.
3. Under **Import Transactions**, tap **Import CSV File**.
4. Select your generated CSV file (e.g. `cashew_import_merged.csv`).
5. The column mapping will auto-match:
   - `Date` ➡️ Date
   - `Amount` ➡️ Amount
   - `Category` ➡️ Category
   - `Title` ➡️ Title
   - `Note` ➡️ Note
   - `Account` ➡️ Account
6. Tap **Import**.

> [!TIP]
> **Credit Card Transfers**: Once imported, merge the `Transfer` category into Cashew's **`Balance Correction`** category (**More** → **Edit, Delete, and Reorder Data** → **Categories** → Select `Transfer` → **Merge Category**). This ensures transfers move account balances with zero net effect on your monthly expense budget!

---

## 🔒 Privacy & Security

Financial privacy is paramount:
- **100% Local Execution**: All processing happens entirely on your local machine. No data is sent over the network.
- **Git Ignored**: `.gitignore` is configured by default to ignore all CSV, PDF, and statement files inside `data/` or any local directory. Your private financial records will never be committed to source control.

---

## 🤝 Contributing

Contributions to expand merchant coverage or support other UAE/GCC banks are warmly welcome!
1. Fork the repository.
2. Add merchant keywords or cleaners to `scripts/convert_to_cashew_csv.py`.
3. Submit a pull request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
