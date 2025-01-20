from bot.config import GigaChatKey
from bot.database_create import get_program_recommendation
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage

LLM = GigaChat(
    credentials=GigaChatKey,
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    verify_ssl_certs=False, 
    streaming=False,
)

response = [
    SystemMessage(
        content="Ты — эксперт по направлениям, твоя задача - задавать пользователю вопросы, анализировать и предлагать наиболее подходящее направление."
    )
]

def get_response(user_message: str) -> str:
    response.append(HumanMessage(content=user_message))
    
    res = LLM.invoke(response)
    
    return res.content
