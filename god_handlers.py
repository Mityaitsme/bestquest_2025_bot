from telebot.handler_backends import State
from telebot.types import ForceReply
from riddle_utils import *
from global_variables import *


def activate_god_handlers():
    @bot.callback_query_handler(
        func=lambda call: (
            call.message.chat.id == GOD_ID
            and call.data
            and call.data.split(":")[0] in ("approve", "reject", "approve+feedback", "reject+feedback")
            and bot.get_state(call.data.split(":")[1], call.data.split(":")[1]) == "State:answer_verification" )
    )
    def answer_verification(call):
        try:
            action, team_id, team_name = call.data.split(":")
            team_id = int(team_id)

            if action == "approve":
                right_answer_scenario(bot, team_id)
                return
            
            elif action == "reject":
                wrong_answer_scenario(bot, team_id)
                return
            
            prompt = bot.send_message(
                GOD_ID,
                f"Напиши текст для команды {team_name} "
                f"(ответ {'одобрен' if action.startswith('approve') else 'отклонён'}). "
                f"Пожалуйста, отвечай именно на это сообщение.",
                reply_to_message_id=call.message.message_id,
                reply_markup=ForceReply(selective=True)
            )
            bot.set_state(team_id, State.verification_feedback, team_id)

            FEEDBACK_MAP[prompt.message_id] = {
                "team_id": team_id,
                "action": action
            }
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Error in answer_verification: {e}")
            bot.answer_callback_query(call.id)


    def needs_manual_reply(msg):
        if msg.chat.id != GOD_ID:
            return False
        if not msg.reply_to_message:
            return False
        if msg.reply_to_message.message_id not in FEEDBACK_MAP:
            return False
        
        state = bot.get_state(
            FEEDBACK_MAP[msg.reply_to_message.message_id]["team_id"],
            FEEDBACK_MAP[msg.reply_to_message.message_id]["team_id"]
        )    
        return state in ["State:verification_feedback", State.verification_feedback]


    @bot.message_handler(
        func=lambda msg: (
            needs_manual_reply(msg)),
        content_types=DEFAULT_CONTENT_TYPES
    )
    def handle_manual_reply(msg):
        data = FEEDBACK_MAP.pop(msg.reply_to_message.message_id)
        team_id = data["team_id"]
        action = data["action"]

        if action == "approve+feedback":
            right_answer_scenario(bot, team_id, feedback=msg)
        else:
            wrong_answer_scenario(bot, team_id, feedback=msg)