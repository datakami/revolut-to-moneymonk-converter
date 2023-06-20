# revolut-to-moneymonk-converter
Export Revolut transaction statements to a csv-format MoneyMonk can understand

Script for transforming Revolut credit card transaction statements to MoneyMonk compatible csv format.

Formatting of output inspired by [https://github.com/adriaanvanrossum/n26-to-moneymonk](https://github.com/adriaanvanrossum/n26-to-moneymonk)

## How to use this:

- Create a MoneyMonk bank account with the IBAN of your Revolut account
- download your Revolut transaction statement as "Excel document" via the Revolut app or website
- define custom rewrites for payee names and description strings (optional)
- run this python script using `python -m converter`. Use `python -m converter -h` to learn about the commandline arguments.

Unfortunately I have not yet found a way to make Revolut work with a MoneyMonk account of type 'credit card'.

The code is pure Python 3 with no dependencies.
