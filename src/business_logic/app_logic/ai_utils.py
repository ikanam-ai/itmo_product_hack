from datetime import datetime

TYPE_DND = "dnd"
TYPE_DEMO_REQ = "demo_req"
TYPE_PRESENTATION_REQ = "present_req"
TYPE_MORE_INFO_REQ = "more_info_req"
TYPE_TIMEOUT_REQ = "timeout_req"
TYPE_REDIRECT_REQ = "redirect_req"
TYPE_UNKNOWN_REQ = "unknown_req"


def generate_incentive_email(name, company_name, products):
    return "subject", "email"


def generate_incentive_tg_mail(name, company_name, products):
    # Шлем инициативное письмо конкретному пользователю
    # ___Нужен импорт функции для отправки конкретному пользователю из tg_utils___
    return "tg message"


def generate_demo_email(name, company_name, message):
    return "No demo today", "Demo is not provided!! Ho-Ho"


# Пользователь попросил демо (письмо с данными для входа в демо)
def generate_demo_tg(name, company_name, message):
    return "Demo is not provided!! HaHa"


def generate_presentation_email(name, company_name, message):
    return "No presentation today", "Presentation is not provided!! He-He"


def generate_presentation_tg(name, company_name, message):
    return "Presentation is not provided!! He-He"


def generate_more_info_email(name, company_name, message):
    return "More info", "Here we keep talking to the client"


def generate_more_info_tg(name, company_name, message):
    return "Here we keep talking to the client"


# Логика с таймаутом
def get_timeout_from_msg(message):
    return datetime.now()


def generate_reminder_email(name, company_name):
    return "Reinder", "You forgot about us!"


def generate_reminder_tg(name, company_name):
    return "You forgot about us!"


def classify_email(message, subject):
    return TYPE_DND


def classify_tg_message(message):
    # Логика с классификацией сообщения (LLM)
    return TYPE_DND