from langchain_google_genai import ChatGoogleGenerativeAI


def initialize_llm(api_key: str):
	return ChatGoogleGenerativeAI(
		model='gemini-2.0-flash-lite',
		api_key=api_key,
		temperature=0.3,
	)
