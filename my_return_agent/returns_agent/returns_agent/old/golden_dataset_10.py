"""10 test questions, and what should be booked after each one."""

#        customer  question                                                     expected
TESTS = [
    ("C-101", "I want to return the kurta I got last week",                "ORD-5001 return approved"),
    ("C-101", "Please return my Sequin Party Dress",                       "nothing"),
    ("C-102", "I want to return my TV",                                    "nothing"),
    ("C-102", "The running shoes are too small, can I get size 7?",        "ORD-5003 exchange approved"),
    ("C-102", "The running shoes are too small, I need size 9",            "nothing"),
    ("C-103", "I want to return the coffee table",                         "ORD-5005 return waiting_for_staff"),
    ("C-104", "I want to return the kurta",                                "nothing"),
    ("C-104", "Please return order ORD-5001",                              "nothing"),
    ("C-104", "I want to return my jeans",                                 "ORD-5008 return approved"),
    ("C-106", "I want to return the Sequin Party Dress I got 2 days ago",  "ORD-5016 return approved"),
]