from langchain_google_genai import GoogleGenerativeAI

llm = GoogleGenerativeAI(model_name="gemini-2.5-flash", api_key="[ENCRYPTION_KEY]")

response = llm.invoke("Hello, how are you?")
print(response.text)