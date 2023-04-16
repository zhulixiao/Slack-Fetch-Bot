import json
from EdgeGPT import Chatbot, ConversationStyle


# wait for user to ask
async def ask(prompt, bot):
    answer = await bot.ask(prompt, conversation_style=ConversationStyle.balanced,wss_link="wss://sydney.bing.com/sydney/ChatHub")    
    # only print the text
    reply = extract_answer_text(answer)

    return reply


def extract_answer_text(data):
    # if the answer is missing, return "I don't know"
    if "item" not in data or "messages" not in data["item"] or len(data["item"]["messages"]) < 2:
        return "Sorry, I don't know the answer."

    answer_message = data["item"]["messages"][1]
    raw_text = answer_message["text"]

    # if sourceAttributions is missing, return the raw text
    if "sourceAttributions" not in answer_message:
        return raw_text
    
    sources = answer_message["sourceAttributions"]
    
    # replace every string of the form "[^number^]" with <sources[number]|[number]> (slack hyperlink)
    for i in range(len(sources)):
        raw_text = raw_text.replace("[^" + str(i+1) + "^]", " <" + sources[i]["seeMoreUrl"] + "|[" + str(i+1) + "]>")

    answer_text = raw_text.replace("**", "*")
    return answer_text


# request the bot
async def request_bot(prompt):

    # if bot exists, use it
    if "bot" in globals():
        bot = globals()["bot"]
    else:
        if prompt == "Exit" or prompt == "exit":
            return "I am not active now. Please ask me something to activate me."
        # create a new bot
        bot = Chatbot()
        globals()["bot"] = bot

    if prompt == "Exit" or prompt == "exit":
        await bot.close()
        # delete the bot
        del globals()["bot"]
        return "Bye! See you next time!"
    
    if prompt == "Inactivity" or prompt == "inactivity":
        await bot.close()
        # delete the bot
        del globals()["bot"]
        return "I am inactive now. Please ask me something to activate me."

    return await ask(prompt, bot)

