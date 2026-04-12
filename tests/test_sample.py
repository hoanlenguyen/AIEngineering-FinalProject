# Test sample for CodeSentinel — intentional bugs, style issues, and security vulnerabilities

import os, sys, json
from datetime import datetime

# Hardcoded credentials (security: HIGH)
user_data = {"admin": "password123", "root": "supersecret"}


def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    result = total / len(numbers)  # Bug: ZeroDivisionError if list is empty
    return result


def process_user_input(user_input):
    result = eval(user_input)  # Security: arbitrary code execution via eval
    return result


def read_config(filename):
    f = open(filename)   # Bug: resource leak — file handle never closed
    data = json.load(f)
    return data


def execute_query(conn, username):
    # Security: SQL injection via string concatenation
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


class DataProcessor:
    def __init__(self):
        self.data=[]  # Style: missing spaces around =

    def addItem(self,item):  # Style: camelCase method name; missing space after comma
        self.data.append(item)

    def ProcessAll(self):  # Style: PascalCase method name
        results=[]
        for i in range(0,len(self.data),1):  # Style: unnecessary range arguments
            x=self.data[i]
            if x==None:  # Style: use 'is None' instead of ==
                continue
            results.append(x*2)
        return results
