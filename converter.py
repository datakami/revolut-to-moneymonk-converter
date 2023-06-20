#!/usr/bin/python

import argparse
import dataclasses
import datetime

from csv import DictReader, DictWriter
from dataclasses import dataclass

from custom_mappings import payee_mapping, description_mapping

REVOLUT_EXPORT_HEADER = "Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance".split(",")
MM_DATE_FORMAT = "%d-%m-%Y"

@dataclass
class RevolutTransaction:
    transaction_type: str # Type
    product: str # Product
    started_date: datetime.datetime # Started Date
    completed_date: datetime.datetime # Completed Date
    description: str # Description
    amount: float # Amount
    fee: float # Fee
    currency: str # Currency
    state: str # State
    balance: float # Balance"
    
    def __init__(self, revolut_row):
        self.transaction_type = revolut_row.get('Type')
        self.product = revolut_row.get('Product')
        self.started_date = datetime.datetime.fromisoformat(revolut_row.get('Started Date'))
        self.completed_date = datetime.datetime.fromisoformat(revolut_row.get('Completed Date'))
        self.description = revolut_row.get('Description')
        self.amount = float(revolut_row.get('Amount'))
        self.fee = float(revolut_row.get('Fee'))
        self.currency = revolut_row.get('Currency')
        self.state = revolut_row.get('State')
        self.balance = float(revolut_row.get('Balance'))
    
    def total_amount(self):
        if self.fee > 0:
            self.fee = -1 * self.fee
        return self.amount + self.fee
        
    def abs_total_amount(self):
        return abs(self.total_amount())
        
    def is_credit(self):
        return self.amount >= 0
        
    def is_debit(self):
        return self.amount < 0
        
    def credit_or_debit(self):
        if self.is_credit():
            return "C"
        return "D"

@dataclass
class MoneyMonkTransaction:
    account_nr: str # Rekeningnummer
    transaction_date: datetime.datetime # Transactiedatum
    currency: str # Valutacode
    credit_debit: str # CreditDebet
    amount: float # Bedrag
    payee_account_nr: str # Tegenrekeningnummer
    payee_name: str # Tegenrekeninghouder
    currency_date: str # Valutadatum
    payment_method: str # Betaalwijze
    description: str # Omschrijving
    transaction_type: str # "Type betaling"
    transfer_auth_nr: str # Machtigingsnummer
    direct_debit_payee_id: str # "Incassant ID"
    address: str # Adres
    reference_nr: str # Referentie
    book_date: str # Boekdatum
    last_column: str # last column is empty: ""

    def __init__(self, revolut_transaction, revolut_iban):
        date = revolut_transaction.started_date.strftime(MM_DATE_FORMAT)
        self.account_nr = revolut_iban
        self.transaction_date = date
        self.currency = revolut_transaction.currency
        self.credit_debit = revolut_transaction.credit_or_debit()
        self.amount = revolut_transaction.abs_total_amount()
        self.payee_account_nr = ''
        self.payee_name = try_mapping(revolut_transaction.description, payee_mapping)
        self.currency_date = date
        self.payment_method = "Credit card"
        self.description = try_mapping(revolut_transaction.description, description_mapping)
        self.transaction_type = "Credit card"
        self.transfer_auth_nr = ''
        self.direct_debit_payee_id = ''
        self.address = ''
        self.reference_nr = ''
        self.book_date = date
        self.last_column = ''

def mm_csv_factory(kv_pairs):
    mapping = {
        'account_nr' : 'Rekeningnummer',
        'transaction_date' : 'Transactiedatum',
        'currency' : 'Valutacode',
        'credit_debit' : 'CreditDebet',
        'amount' : 'Bedrag',
        'payee_account_nr' : 'Tegenrekeningnummer',
        'payee_name' : 'Tegenrekeninghouder',
        'currency_date' : 'Valutadatum',
        'payment_method' : 'Betaalwijze',
        'description' : 'Omschrijving',
        'transaction_type' : 'Type betaling',
        'transfer_auth_nr' : 'Machtigingsnummer',
        'direct_debit_payee_id' : 'Incassant ID',
        'address' : 'Adres',
        'reference_nr' : 'Referentie',
        'book_date' : 'Boekdatum',
        'last_column' : ''
    }        
    return {mapping.get(k) : v for k, v in kv_pairs}

# postprocess some strings using a custom mapping
# defined in custom_mappings.py 
def try_mapping(s, mapping):
    if s in mapping.keys():
        return mapping.get(s)
    return s

        
def main(revolut_iban, revolut_export_file, output_filename=None):
    # read revolut statement
    revolut_transactions = []
    with open(revolut_export_file,'r') as csvfile:
        # we're using fieldnames param 
        # because we want an error if the csv has a different format than we expect
        reader = DictReader(csvfile, fieldnames=REVOLUT_EXPORT_HEADER)
        next(reader)
        for row in reader:
            revolut_transactions.append(RevolutTransaction(row))

    # convert revolut transactions to moneymonk transactions
    moneymonk_transactions = []
    for revolut_transaction in revolut_transactions:
        mm_transaction = MoneyMonkTransaction(revolut_transaction, revolut_iban)
        moneymonk_transactions.append(mm_transaction)
     
    # write moneymonk transactions to file 
    moneymonk_csv_rows = []
    for mm_transaction in moneymonk_transactions:
        row_data = dataclasses.asdict(mm_transaction, dict_factory=mm_csv_factory)
        moneymonk_csv_rows.append(row_data)
    
    if not output_filename:
        output_filename = revolut_export_file + ".mm.csv"

    with open(output_filename, 'w', newline='') as outfile:
        fieldnames = list(moneymonk_csv_rows[0].keys())
        writer = DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in moneymonk_csv_rows:
            writer.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='Revolut to MoneyMonk converter',
                    description='Converter for turning Revolut transaction statements (CSV) into a format (CSV) that can be imported in a MoneyMonk bank account',
                    epilog='Datakami, June 2023')
    parser.add_argument('-b', '--iban', dest='iban', required=True, help="IBAN number of you revolut bank account")         
    parser.add_argument('-i', '--input', dest='input_filename', required=True, help="filename of a Revolut statement as csv")      # option that takes a value
    parser.add_argument('-o', '--output', dest='output_filename', help='filename of output csv file')     # option that takes a value
    args = parser.parse_args()
    main(revolut_iban=args.iban, revolut_export_file=args.input_filename, output_filename=args.output_filename)
