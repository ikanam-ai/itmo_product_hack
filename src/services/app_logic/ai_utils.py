from datetime import datetime

TYPE_DND = "dnd"
TYPE_DEMO_REQ = "demo_req"
TYPE_PRESENTATION_REQ = "present_req"
TYPE_MORE_INFO_REQ = "more_info_req"
TYPE_TIMEOUT_REQ = "timeout_req"
TYPE_REDIRECT_REQ = "redirect_req"
TYPE_UNKNOWN_REQ = "unknown_req"


def generate_incentive_email(name, company_name, products):
    print(
        "generate_incentive_email name",
        name,
        "company_name",
        company_name,
        "products",
        products,
    )
    return "subject incentive", "email incentive"


def generate_incentive_tg_mail(name, company_name, products):
    print(
        "generate_incentive_tg_mail name",
        name,
        "company_name",
        company_name,
        "products",
        products,
    )
    return "tg message incentive"


def generate_demo_email(name, company_name, message):
    print(
        "generate_demo_email name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    return "No demo today", "Demo is not provided!! Ho-Ho"


def generate_demo_tg(name, company_name, message):
    print(
        "generate_demo_tg name", name, "company_name", company_name, "message", message
    )
    return "Demo is not provided!! HaHa"


def generate_presentation_email(name, company_name, message):
    print(
        "generate_presentation_email name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    return "No presentation today", "Presentation is not provided!! He-He"


def generate_presentation_tg(name, company_name, message):
    print(
        "generate_presentation_tg, name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    return "Presentation is not provided!! He-He"


def generate_more_info_email(name, company_name, message):
    print(
        "generate_more_info_email name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    return "More info", "Here we keep talking to the client"


def generate_more_info_tg(name, company_name, message):
    print(
        "generate_more_info_tg name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    return "Here we keep talking to the client"


def get_timeout_from_msg(message):
    print("get_timeout_from_msg message", message)
    return datetime.now()


def generate_reminder_email(name, company_name):
    print("generate_reminder_email name", name, "company_name", company_name)
    return "Reminder", "You forgot about us!"


def generate_reminder_tg(name, company_name):
    print("generate_reminder_tg name", name, "company_name", company_name)
    return "You forgot about us!"


def classify_email(message, subject):
    print("classify_email message", message, "subject", subject)
    # return TYPE_DND
    # return TYPE_DEMO_REQ
    # return TYPE_PRESENTATION_REQ
    # return TYPE_TIMEOUT_REQ
    # return TYPE_REDIRECT_REQ
    return TYPE_UNKNOWN_REQ


def classify_tg_message(message):
    print("classify_tg_message message", message)
    return TYPE_DND
