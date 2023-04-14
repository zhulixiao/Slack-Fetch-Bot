import asyncio
from EdgeGPT import Chatbot, ConversationStyle


# wait for user to ask
async def ask(prompt, bot):
    while True:
        question = input(prompt)
        if question == "exit":
            break
        answer = await bot.ask(question, conversation_style=ConversationStyle.creative,wss_link="wss://sydney.bing.com/sydney/ChatHub")
        # only print the text
        reply = extract_answer_text(answer)
        print(reply)


def extract_answer_text(data):
    answer_message = data["item"]["messages"][1]
    raw_text = answer_message["text"]
    sources = answer_message["sourceAttributions"]

    # replace every string of the form "[^number^]" with <sources[number]|[number]> (slack hyperlink)
    for i in range(len(sources)):
        raw_text = raw_text.replace("[^" + str(i+1) + "^]", "<" + sources[i]["seeMoreUrl"] + "|[" + str(i) + "]>")

    answer_text = raw_text.replace("**", "*")
    return answer_text


if __name__ == "__main__":
    bot = Chatbot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ask("You: ", bot))
    loop.close()
