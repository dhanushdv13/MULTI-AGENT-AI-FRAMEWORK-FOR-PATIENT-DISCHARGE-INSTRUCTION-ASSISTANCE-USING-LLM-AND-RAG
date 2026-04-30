import asyncio
async def test():
    from features.chat.agent_router import AgentRouter
    router = AgentRouter()
    try:
        result = await router.ask('vec_a39222941dc124b5b8a3fe1249645a49a', 'What should I eat?')
        print(result)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(test())