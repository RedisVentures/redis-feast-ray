import requests
import json
body = {"zipcode": [76104],
        "person_age": [22],
        "person_income": [59000],
        "person_home_ownership": ["RENT"],
        "person_emp_length": [123.0],
        "loan_intent": ["PERSONAL"],
        "loan_amnt": [35000],
        "loan_int_rate": [16.02],
        "dob_ssn": ["19530219_5179"]
    }

response = requests.get(f"http://localhost:8000/LoanModel/loan", json=body)

print(response.text)
