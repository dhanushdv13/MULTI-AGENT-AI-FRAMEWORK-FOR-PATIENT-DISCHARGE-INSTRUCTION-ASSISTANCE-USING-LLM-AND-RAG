import asyncio
async def test():
    from features.chat.agent_router import AgentRouter
    router = AgentRouter()
    try:
        # result = await router.ask('vec_702caaa6ae2544129f33c83cda7f0f0e', 'validate the bill')
        # result = await router.ask('vec_702caaa6ae2544129f33c83cda7f0f0e', 'Check the price of Enoxaparin')
        # result = await router.ask('new_temp', 'Give me discharge summary')
        result = await router.ask('new_temp', 'Give me Diet Plan')
        print(result)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(test())
