import os
import time
from datetime import datetime
from pymongo import MongoClient

RESPONSE_FIELD = 'model_response'
CLASS_FIELD = 'response_class'
CONTACTS_FIELD = 'contacts'
ATTACHMENT_FIELD = "need_image"

IMAGE_FOLDER = "info_images"

# as we didn't get resources for GPU on Yandex cloud, we host the model (see model.py) on our own infrastructure
LLM_MONGO_USERNAME = os.getenv('MONGO_LLM_INITDB_ROOT_USERNAME')
LLM_MONGO_PASSWORD = os.getenv('MONGO_LLM_INITDB_ROOT_PASSWORD')
LLM_MONGO_HOST = os.getenv('MONGO_LLM_HOST')
LLM_MONGO_PORT = os.getenv('MONGO_LLM_INITDB_ROOT_PORT')

mongo_uri = f"mongodb://{LLM_MONGO_USERNAME}:{LLM_MONGO_PASSWORD}@{LLM_MONGO_HOST}:{LLM_MONGO_PORT}/"
client = MongoClient(mongo_uri)
db = client['llm_database']
collection = db['dataset_ai']


def add_task(task_data, model):
    task = {
        "model": model,
        "prompt": task_data['prompt'],
        "status": "pending",
        "response": None
    }
    task.update(task_data)  
    result = collection.insert_one(task)
    print(f"Added task with id: {result.inserted_id}")
    return result.inserted_id


def wait_for_task_completion(task_id, timeout=300, check_interval=5):
    """
    Ожидает завершения задачи в течение заданного времени.
    
    :param task_id: ID задачи в базе данных
    :param timeout: Максимальное время ожидания (в секундах)
    :param check_interval: Интервал проверки статуса задачи (в секундах)
    :return: Результат выполнения задачи или сообщение об ошибке
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Поиск задачи по ID в коллекции
        task = collection.find_one({"_id": task_id})
        
        if task:
            status = task.get('status')
            if status == 'completed':
                # Забираем response при завершении
                return task.get('response')
            elif status == 'failed':
                return {"Ошибка": "Задача завершилась с ошибкой"}
        else:
            return {"Ошибка": "Задача не найдена"}
        
        # Ждем перед следующей проверкой
        time.sleep(check_interval)
    
    return {"Ошибка": "Превышено время ожидания завершения задачи"}


TYPE_DND = "dnd" 
TYPE_DEMO_REQ = "demo_req" 
TYPE_PRESENTATION_REQ = "present_req"
TYPE_TIMEOUT_REQ = "timeout_req" 
TYPE_REDIRECT_REQ = "redirect_req"
TYPE_UNKNOWN_REQ = "unknown_req"
TYPE_MORE_INFO_REQ = "need_more_info"


def extract_information(text: str) -> dict:
    model = 'qwen2:72b-instruct-q4_0'
    try:
        # Добавляем задачу в базу
        task_id = add_task({"prompt": text}, model)
        
        # Ожидаем завершения задачи и забираем результат
        result = wait_for_task_completion(task_id)
        
        return result
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        return {"Ошибка": "Не удалось обработать запрос"}


def generate_incentive_email(name, company_name, products):
    print(
        "generate_incentive_email name",
        name,
        "company_name",
        company_name,
        "products",
        products,
    )
    template = """Добрый день!

Меня зовут Роман, я представляю Napoleon IT. Рад знакомству!

Зная, что ваша компания, Tasty Coffee, успешно занимается продажей кофе на маркетплейсах, хочу предложить решение, которое может помочь вам ещё лучше понимать своих клиентов и оптимизировать их опыт взаимодействия с вашим брендом.

Наш AI-инструмент уже помогает таким компаниям, как 12 STOREEZ, Lapochka и Cotton Club, улучшать customer experience и выстраивать более эффективные маркетинговые стратегии на основе анализа отзывов. Учитывая специфику работы Tasty Coffee на маркетплейсах, наша система может быть полезна вам в следующих аспектах:

- Анализ обратной связи на маркетплейсах: Систематизируйте отзывы и комментарии клиентов, чтобы глубже понимать, как они оценивают ваш продукт и процесс покупки.
- Оптимизация качества продукта и сервиса: Выявляйте основные аспекты, которые клиенты ценят, и улучшайте то, что требует доработки, будь то вкусовые качества кофе или скорость доставки.
- Конкурентный анализ: Отслеживайте отзывы о продуктах конкурентов на тех же маркетплейсах, чтобы находить возможности для улучшения и роста.
- Управление ассортиментом: Получайте данные о том, какие виды кофе наиболее востребованы, и оперативно реагируйте на изменения в предпочтениях клиентов.

Мы с радостью проведём демо, чтобы показать, как наша система поможет Tasty Coffee повысить лояльность покупателей и улучшить позиции на маркетплейсах. Напишите, когда вам удобно обсудить это более подробно.

    """
    return "Наполеон IT Отзывы", template


def generate_incentive_tg_mail(name, company_name, products):
    print(
        "generate_incentive_tg_mail name",
        name,
        "company_name",
        company_name,
        "products",
        products,
    )
    return generate_incentive_email(name, company_name, products)[1]


def generate_demo_email(name, company_name, message):
    print(
        "generate_demo_email name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    template = """
Подтверждение назначение Демо показа продукта. Время:%s 

Буду рад продемонстрировать, как наш AI-инструмент может помочь вашей компании улучшить клиентский опыт и оптимизировать продажи на маркетплейсах.

До встречи!

С уважением,  
Команда Napoleon IT.Отзывы
    """
    return "Napoleon IT.Отзывы", template % str(datetime.now())


def generate_demo_tg(name, company_name, message):
    print(
        "generate_demo_tg name", name, "company_name", company_name, "message", message
    )
    return generate_demo_email(name, company_name, message)[1]


def generate_presentation_email(name, company_name, message):
    print(
        "generate_presentation_email name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    template = """Высылаю презентацию нашего продукта.

С уважением,  
Роман, Napoleon IT.Отзывы
"""
    return "Napoleon IT.Отзывы", template


def generate_presentation_tg(name, company_name, message):
    print(
        "generate_presentation_tg, name",
        name,
        "company_name",
        company_name,
        "message",
        message,
    )
    return generate_presentation_email(name, company_name, message)[1]


def get_timeout_from_msg(message):
    print("get_timeout_from_msg message", message)
    date_str = message.get('date', '01-01-2040')
    date_format = "%d-%m-%Y"
    date_obj = datetime.strptime(date_str, date_format)
    return date_obj


def generate_reminder_email(name, company_name):
    print("generate_reminder_email name", name, "company_name", company_name)
    template = """Здравствуйте!

Ранее мы обсуждали возможность пообщаться о нашем продукте для вашей компании. Напомню, что наша AI-платформа уже помогает таким брендам, как 12 STOREEZ, Lapochka и Cotton Club, оптимизировать клиентский опыт и улучшать результаты на основе анализа отзывов и обратной связи.

Будет здорово вернуться к обсуждению и подробнее рассмотреть, как наш инструмент может быть полезен для вашей компании. Если вам удобно, можем назначить демо на ближайшее время.

Буду рад вашему ответу!

С уважением,  
Роман  
Napoleon IT
"""
    return "Napoleon IT. Отзывы", template


def generate_reminder_tg(name, company_name):
    print("generate_reminder_tg name", name, "company_name", company_name)
    return generate_reminder_email(name, company_name)[1]


def get_response_from_date(data):
    resp = data.get(RESPONSE_FIELD, "no response")
    resp = resp.replace("\\n", "\n")
    return "Наполеон IT.Отзывы", resp


def get_response_attachment(response_data):
    attachment_name = response_data.get(ATTACHMENT_FIELD, None)
    if attachment_name:
        try:
            f_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), IMAGE_FOLDER, attachment_name)
            if os.path.exists(f_path):
                with open(f_path, "rb") as fd:
                    attachment_content = fd.read()

                return attachment_content, attachment_name
        except Exception as e:
            print("Got exception in get_response_attachment", e)

    return None, None


def get_contacts_from_data(data):
    return data.get(CONTACTS_FIELD, None)


def classify_email(message, subject):
    data = extract_information(message)
    if RESPONSE_FIELD not in data or CLASS_FIELD not in data:
        print("Invalid model response", data)
        return TYPE_UNKNOWN_REQ, data

    print("message processed:", data)
    response_class = TYPE_UNKNOWN_REQ
    data_class = data[CLASS_FIELD]
    
    # Определяем тип запроса на основе response_class
    if data_class == '1':
        response_class = TYPE_DND
    elif data_class == '2':
        response_class = TYPE_DEMO_REQ
    elif data_class == '3':
        response_class = TYPE_PRESENTATION_REQ
    elif data_class == '4':
        response_class = TYPE_TIMEOUT_REQ
    elif data_class == '5':
        response_class = TYPE_REDIRECT_REQ
    elif data_class == '7':
        response_class = TYPE_MORE_INFO_REQ

    return response_class, data


def classify_tg_message(message):
    return classify_email(message, "no_subject")
