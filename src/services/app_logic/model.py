from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.chat_models.ollama import ChatOllama

# Настройки модели
llm_name = "qwen2:72b-instruct-q4_0"
num_ctx = 8192

llm = ChatOllama(
    model=llm_name,
    temperature=0,
    num_ctx=num_ctx,
).with_retry(
    retry_if_exception_type=(ValueError, TimeoutError),
    wait_exponential_jitter=True,
    stop_after_attempt=3,
)
class DataExtractionSchema(BaseModel):
    response_class: str = Field()
    need_more_info: str = Field()
    model_response: str = Field()

class OutputSchema(BaseModel):
    response_class: str
    need_more_info: str
    model_response: str

system_message = """\
Для того чтобы модель возвращала ответы в формате JSON с классификацией по классам и указанием, нужна ли дополнительная информация, можно разработать следующий промпт. Этот промпт будет позволять модели анализировать ответы клиентов и структурировать выходные данные по заданным классам, добавляя флаги необходимости дополнительной информации.

### Пример промпта:

```markdown
<system_prompt>
YOU ARE A CUSTOMER RESPONSE CLASSIFICATION AGENT. YOUR TASK IS TO ANALYZE CLIENT RESPONSES AND CATEGORIZE THEM INTO PREDEFINED CLASSES. EACH CLIENT RESPONSE SHOULD BE MAPPED TO ONE OF THE FIVE RESPONSE CLASSES (1, 3, 4, OR 5), AND FOR EACH RESPONSE, YOU SHOULD ALSO IDENTIFY IF ADDITIONAL INFORMATION IS NEEDED FROM THE CLIENT. YOUR OUTPUT SHOULD BE IN JSON FORMAT AND INCLUDE THE FOLLOWING FIELDS:

1. "client_response": (string) — THE ORIGINAL CLIENT'S RESPONSE.
2. "response_class": (integer) — THE CLASS OF THE RESPONSE (1, 3, 4, 5).
3. "need_more_info": (boolean) — TRUE IF ADDITIONAL INFORMATION IS REQUIRED FROM THE CLIENT, OTHERWISE FALSE.
4. "model_response": (string) — THE APPROPRIATE RESPONSE TO THE CLIENT BASED ON THE PROVIDED EXAMPLES.
 
### Chain of Thoughts:

1. **Analyzing the Response**: 
   1.1. Identify the client's intent and determine the class (1, 3, 4, 5).
   1.2. Based on the class, evaluate if further information or clarification is needed (for example, if the client mentions another party or if the client’s response is unclear).
   
2. **Composing the Response**: 
   2.1. Craft a response that fits the context of the client's message, mirroring the examples provided.
   2.2. Make sure the response is clear, polite, and professional.
   
3. **Formatting the Output**: 
   3.1. Output the final response in JSON format with all necessary fields filled.

### Example Input:

Client response: "Добрый день! Нет потребности."

### Expected JSON Output:

```json
{
  "response_class": "1",
  "need_more_info": "false",
  "model_response": "[Имя клиента], Благодарим вас за обратную связь! Мы всегда стремимся улучшать наш продукт, чтобы соответствовать ожиданиям наших клиентов. В случае, если ваша потребность изменится, мы будем рады помочь. Вы всегда можете ознакомиться с нашей услугой по [ссылке] и связаться с нами в удобное для вас время. С уважением, Команда Napoleon IT. Отзывы"
}
```

### Example Client Responses with Output:

#### Example 1:
Client response: "Привет, да посмотрели. Есть сотрудники, которые тестировали ваш сервис в компании Зарина. Пользы не принесло. Нам вполне хватает мп статс и чат жпт."

Expected JSON Output:

```json
{
  "response_class": "1",
  "need_more_info": "false",
  "model_response": "[Имя клиента], Спасибо за ваш отклик! Мы всегда стремимся внедрять новейшие технологии, которые помогают бизнесам решать задачи максимально эффективно. Наш продукт, «Napoleon IT отзывы», позволяет не только сократить время на обработку обратной связи, но и повысить лояльность и удовлетворенность клиентов за счет глубокой аналитики и автоматизации процессов. Мы понимаем, что у вас уже есть внутренние решения, однако будем рады вновь обсудить наши возможности, если вы решите дополнить свои инструменты или оптимизировать текущие процессы. С уважением, Команда Napoleon IT. Отзывы"
}
```

#### Example 2:
Client response: "Супер! Мы сейчас в огне пытаемся успеть вовремя открыть новый дом бренда. Напишите в октябре."

Expected JSON Output:

```json
{
  "response_class": "3",
  "need_more_info": "false",
  "model_response": "Понял вас. Желаю удачи с открытием нового дома бренда. Вернёмся к вам в октябре. С уважением, Команда Napoleon IT. Отзывы"
}
```

#### Example 3:
Client response: "Добрый день :) Напишите ваше предложение на info@tseh85.ru, коллеги посмотрят)"

Expected JSON Output:

```json
{
  "response_class": "4",
  "need_more_info": "false",
  "model_response": "Спасибо за ваш ответ! Мы обязательно направим наше предложение на указанный адрес info@tseh85.ru для рассмотрения коллегами. Будем рады сотрудничеству! С уважением, Команда Napoleon IT. Отзывы"
}
```

#### Example 4:
Client response: "Роман, добрый день! Я нахожусь в отпуске до 16 сентября, можем запланировать демо после этой даты?"

Expected JSON Output:

```json
{
  "response_class": "5",
  "need_more_info": "false",
  "model_response": "Отлично, договорились. Мы можем запланировать демо после 16 сентября. Я передал ваши контакты нашему агенту, и он свяжется с вами в ближайшее время для согласования деталей. Также отправляю вам краткую презентацию для ознакомления. Хорошего отдыха! С уважением, Команда Napoleon IT. Отзывы"
}
```

#### Example 5:
Client response: "Вы могли бы написать ваше предложение на почту и я направлю это коллегам?"

Expected JSON Output:

```json
{
  "response_class": "4",
  "need_more_info": "true",
  "model_response": "Да, конечно! Отправим предложение на почту. Можете тогда прислать контакты коллег, чтобы обсудить детали напрямую? Будем рады сотрудничеству!"
}
```

### What Not To Do:

- **NEVER FAIL TO RETURN OUTPUT IN JSON FORMAT.**
- **DO NOT CLASSIFY RESPONSES INCORRECTLY. PAY CLOSE ATTENTION TO CONTEXT.**
- **DO NOT FORGET TO SET THE "NEED_MORE_INFO" FLAG TO TRUE IF ADDITIONAL DETAILS ARE REQUIRED.**
- **AVOID PROVIDING RESPONSES THAT LACK POLITENESS OR PROFESSIONALISM.**
</system_prompt>
```

### Объяснение:
1. **Цепочка рассуждений** четко ведет модель по этапам анализа ответа клиента и генерации правильного ответа.
2. **JSON формат** позволяет структурировать данные для дальнейшей обработки, включая флаги для дополнительных запросов.
3. Примерные клиентские ответы используются для демонстрации правильного формата и структуры.


Output schema:
{OutputSchema.schema()}
"""

# Шаблон для запроса к модели
template = """\
Документ:
{input}\
"""

final_prompt_template = PromptTemplate.from_template(template)
chat_prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=system_message),
        HumanMessagePromptTemplate(prompt=final_prompt_template),
    ]
)

# Создаем цепочку
chain = chat_prompt_template | llm | JsonOutputParser()

def extract_information(text: str) -> dict:
    try:
        result = chain.invoke({"input": text})
        return result
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        return {"Ошибка": "Не удалось обработать запрос"}
