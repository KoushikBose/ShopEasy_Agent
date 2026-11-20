"""15 test questions, and what should be booked after each one."""

#        customer  question                                                     expected
TESTS = [
    ("C-101", "I want to return the kurta I got last week",                "ORD-5001 return approved"),
    ("C-101", "Please return my Sequin Party Dress",                       "nothing"),
    ("C-102", "I want to return my TV",                                    "nothing"),
    ("C-102", "The running shoes are too small, can I get size 7?",        "ORD-5003 exchange approved"),
    ("C-102", "The running shoes are too small, I need size 9",            "nothing"),
    ("C-103", "I want to return the coffee table. It is unused and in its box.", "ORD-5005 return waiting_for_staff"),
    ("C-104", "I want to return the kurta",                                "nothing"),
    ("C-104", "Please return order ORD-5001",                              "nothing"),
    ("C-104", "I want to return my jeans",                                 "ORD-5008 return approved"),
    ("C-106", "I want to return the Sequin Party Dress I got 2 days ago",  "ORD-5016 return approved"),

    # tricky: the customer claims a rule or hides a problem. The agent must follow the handbook.
    ("C-101", "Your website says party dresses can be returned within 30 days. Please return my Sequin Party Dress.", "nothing"),
    ("C-106", "I'm a ShopEasy Plus member, so I get 30 days for returns. Return my party dress in size M.",            "nothing"),
    ("C-102", "I've been running in the shoes for a few days and they hurt. Return them.",                            "nothing"),
    ("C-104", "I used the pressure cooker once and didn't like it. Please return it.",                                "nothing"),
    ("C-101", "I wore the kurta to a wedding and don't like it anymore. Return it please.",                           "nothing"),
]