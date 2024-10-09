from datetime import datetime
import os
import re
import logging
from typing import List, Optional


from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import StructuredTool
from langchain_core.callbacks.manager import CallbackManager
from langchain.schema import Document
import json
from complex_agent.tools import aget_car_attributes, aget_price_range
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"
TEMPERATURE_MAIN_AGENT = 0.25
logger.info(f"Using LLM model: {MODEL} with temperature {TEMPERATURE_MAIN_AGENT}")
llm = ChatOpenAI(model=MODEL, temperature=TEMPERATURE_MAIN_AGENT)


class ComplexAgent:
    def __init__(
        self,
    ):

        self.tools = [
            StructuredTool.from_function(
                coroutine=aget_car_attributes,
                name="Get Car Attributes Values",
                handle_tool_error=True,
            ),
            StructuredTool.from_function(
                coroutine=aget_price_range,
                name="Get Price Range from attribute values",
                handle_tool_error=True,
            ),
        ]

        base_prompt = """Sos un asistente de ventas de autos. Tu tarea es ayudar a clientes y vendedores de autos a encontrar rangos de precios para determinados subconjuntos de autos.
Cuando te pregunten por el rango de precios de un auto, siempre seguir una cadena de 3 pasos:

1) llamar primero a la tool "Get Car Attributes Values" para obtener los posibles valores de los atributos de un auto.
2) Luego, filtrar los valores de cada atributo que tengan sentido con el pedido del usuario. 
3) Por último, llamar a la tool "Get Price Range from attribute values" para obtener el rango de precios de los autos que coinciden con esos valores.

EJEMPLO:
Si te preguntan "rango de precios de un Toyota Corolla 2020",
1) primero llamar a la tool "Get Car Attributes Values" con atributos ["marca", "modelo", "year"].
2) De los posibles valores de cada atributo, filtrar los que interesan de acuerdo a la query del usuario. Por ejemplo marca solo nos interesa "Toyota" u otras formas escritas de la misma palabra, como "TOYOTA".
3) Por último, llamar "Get Price Range from attribute values" con los atributos y valores que nos interesan. Por ejemplo {"marca": ["Toyota", "TOYOTA"], "modelo": ["Corolla"], "year": ["2020"]}.
"""

        base_prompt += f"\n La fecha de hoy es {datetime.today().strftime('%Y-%m-%d')}. Todas las referencias de tiempo que mencione el usuario deben ser calculadas a partir de esta fecha. Todo lo que haya pasado antes de hoy, se debe contar en pasado y aclarar la fecha en la que esté situado el hecho. Si el usuario no menciona ningún marco de tiempo específico, responde al día de hoy."

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", base_prompt),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        agent = create_tool_calling_agent(llm, self.tools, prompt)

        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
        )

        self.runnable = RunnableWithMessageHistory(
            executor,
            crud.get_chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="user_id",
                    annotation=str,
                    name="User ID",
                    description="Unique identifier for the user.",
                    default="",
                    is_shared=True,
                ),
                ConfigurableFieldSpec(
                    id="conversation_id",
                    annotation=str,
                    name="Conversation ID",
                    description="Unique identifier for the conversation.",
                    default="",
                    is_shared=True,
                ),
            ],
        )

    async def ask(
        self,
        query,
        user_id=None,
        conversation_id=None,
    ) -> dict:
        self.user_query = query

        # Assuming `invoke` is also an asynchronous method now
        output = await self.runnable.ainvoke(
            {"input": query},
            config={
                "configurable": {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                },
            },
        )

        return output["output"]
