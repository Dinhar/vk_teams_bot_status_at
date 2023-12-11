import json
import os
import re
from bot.bot import Bot, Event
from bot.handler import MessageHandler, BotButtonCommandHandler

TOKEN = "bot_token"

bot = Bot(token=TOKEN)

projects_urls = {
    'project_name': 'id_group_in_vk_teams'
}

common_chat_id = 'common_chat_id'

def create_data_dictionary(event: Event) -> dict:
    data_ci: str = event.data['text']

    dictionary = {}
    for item in data_ci.split(','):
        key, value = item.split('=')
        dictionary[key] = value

    return dictionary

def define_project(project_name: str) -> str:
    pattern = re.compile("([a-zA-Z0-9-]+)$")
    project_name = pattern.search(project_name)
    return project_name.group(0)

def count_failed_tests_message(count_tests: str) -> None:
    count_failed_tests, count_all_tests = count_tests.split("/")
    failed_tests = f"({count_failed_tests} из {count_all_tests})"

    return failed_tests

def define_status_tests(status: str, count_tests: str) -> str:
    if status == "success":
        return "✅Тесты прошли успешно"
    else:
        if count_tests is None:
            return "❌Тесты провалились"
        else:
            return f"❌Тесты провалились {count_failed_tests_message(count_tests)}"
    
def pre_to_text(*args) -> str:
    text = "\n".join(args)
    return f"<p>{text}</p>"

def build_mr_message(data: dict, project_name: str) -> dict:
    user = f"@[{data['user']}@<domain>]"
    project = f"Проект: <b>{project_name.upper()}</b>"
    branch = f"Ветка: <b>{data['branch']}</b>"

    data = {
        "user": user,
        "project": project,
        "branch": branch,
    }

    return data

def build_message(data: dict, project_name: str) -> str:
    report_url = f"<report_domain>/allure/{data['report_url']}"
    if "count_tests" in data:
        status_at = define_status_tests(data["status"], data["count_tests"])
    else:
        status_at = define_status_tests(data["status"], None)
    report = f'Ссылка на <a href="{report_url}">отчёт</a>'

    if data["branch"]:
        mr_data = build_mr_message(data, project_name)
        text = "\n".join([mr_data["user"], status_at, mr_data["project"], mr_data["branch"], report])
    else:
        text = "\n".join([status_at, report])

    return text

def get_chat_id(data: dict, project_name: str) -> str:
    if data["repo"] == "autotest" and data["branch"]:
        chat_id = common_chat_id
    elif (data["repo"] == "autotest" and data["branch"] == "") or (data["repo"] != "autotest"):
        chat_id = projects_urls[project_name]

    return chat_id

def buttons_answer_cb(bot: Bot, event: Event):
    if event.data['callbackData'] == "call_back_<project_name>":
        os.system('send_curl')

    bot.send_text(event.from_chat, text="Тесты запущены")

def message_cb(bot: Bot, event: Event) -> None:
    data = create_data_dictionary(event)
    project_name = define_project(data["project_name"])
    chat_id = get_chat_id(data, project_name)
    text = build_message(data, project_name)

    if chat_id == common_chat_id:
        bot.send_text(chat_id=chat_id, text=text, parse_mode="HTML")
    else:
        bot.send_text(chat_id=chat_id, text=text, inline_keyboard_markup="{}".format(json.dumps([[
                    {"text": "Запустить АТ", "callbackData": f"call_back_{project_name}", "style": "primary"},
                ]])), parse_mode="HTML")
        

bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
bot.dispatcher.add_handler(BotButtonCommandHandler(callback=buttons_answer_cb))
bot.start_polling()
bot.idle()
