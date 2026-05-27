import os
import logging
from markdown import markdown

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'static/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def agentic_log_analysis(log_file, user_query="Review the latest logs, check for critical events, and outline the general day stats."):
    try:
        from langchain.agents import initialize_agent, Tool, AgentType
        from langchain_openai import ChatOpenAI
        from langchain_community.document_loaders import TextLoader
        from langchain.indexes import VectorstoreIndexCreator
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from markdown import markdown
    except Exception:
        return "<p>Missing Langchain dependencies. Install langchain extras to enable agentic analysis.</p>"

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "<p>OPENROUTER_API_KEY not configured</p>"

    try:
        llm = ChatOpenAI(api_key=api_key, base_url='https://openrouter.ai/api/v1', model='deepseek/deepseek-chat:free', temperature=0)
        loader = TextLoader(log_file, encoding='utf-8')
        embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        index = VectorstoreIndexCreator(embedding=embeddings).from_loaders([loader])

        def search_log_index(query):
            return index.query(query, llm=llm)

        from .summarizer import detect_events, generate_daily_report

        tools = [
            Tool(name='Search Log Index', func=search_log_index, description='Queries the vector store of indexed logs.'),
            Tool(name='Track Critical Events', func=lambda _: detect_events(log_file), description='Run rule-based scan'),
            Tool(name='Generate Daily Report Stats', func=lambda _: generate_daily_report(log_file), description='Generate top keywords')
        ]

        agent = initialize_agent(tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=False)
        response = agent.run(user_query)
        html_response = markdown(response)
        with open(os.path.join(OUTPUT_DIR, 'agentic_analysis.txt'), 'w', encoding='utf-8') as f:
            f.write(response)
        return html_response

    except Exception as e:
        logging.exception('agentic_log_analysis error')
        error_msg = f"Agent workflow failed: {str(e)}"
        with open(os.path.join(OUTPUT_DIR, 'agentic_analysis.txt'), 'w', encoding='utf-8') as f:
            f.write(error_msg)
        return f"<p>{error_msg}</p>"
