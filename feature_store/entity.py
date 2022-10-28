from feast import Entity

zipcode = Entity(
    name="zipcode",
    join_keys=["zipcode"],
    description="Zipcode for the loan origin"
)

dob_ssn = Entity(
    name="dob_ssn",
    join_keys=["dob_ssn"],
    description="Date of birth and last four digits of social security number"
)