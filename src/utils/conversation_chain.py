# src/utils/conversation_chain.py
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from src.services.llm_manager import get_llm
from src.config.logger import logger

PROMPT_TEMPLATE = """
As an academic assistant, answer the question using ONLY the provided context.
Guidelines:
1. Preserve original notation for formulas
2. Cite section numbers when possible
3. For author queries, check metadata first
4. Format with Markdown: headings, bullet points, tables
5. Be concise but thorough

Context: {context}

Question: {question}

Answer:
"""

def get_conversation_chain(vectorstore, use_ollama=False):
    llm = get_llm(use_ollama=use_ollama)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key='answer')
    custom_prompt = PromptTemplate(input_variables=["context", "question"], template=PROMPT_TEMPLATE)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        chain_type="stuff",
        combine_docs_chain_kwargs={"prompt": custom_prompt},
        return_source_documents=True,
        get_chat_history=lambda h: h
    )
    logger.info("Conversation chain created")
    return chain
