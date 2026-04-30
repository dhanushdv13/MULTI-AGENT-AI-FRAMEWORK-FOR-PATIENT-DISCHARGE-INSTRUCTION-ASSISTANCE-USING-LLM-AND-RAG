from multi_agent import MultiAgent

vectorstore = "temp_vectorstore"

agent_system = MultiAgent(vectorstore)

response = agent_system.invoke("Give me Diet Plan")
print(response["messages"][-1].content)
# response = agent_system.diet_agent.invoke("Give me Diet Plan")
# print(response["messages"][-1].content)
print("\n\n\n\n\n\n\n")
# response = agent_system.invoke("Give me Discharge Summary")
# print(response["messages"][-1].content)
# print("\n\n\n\n\n\n\n")
# response = agent_system.invoke("Explain the medical term in above discharge summary and give readable summary")
# print(response["messages"][-1].content)