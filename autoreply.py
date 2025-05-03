from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telethon.sync import TelegramClient
from telethon import TelegramClient, events
from telethon.tl.types import User, Chat, MessageMediaPhoto, MessageMediaDocument
from telethon.errors.rpcerrorlist import AuthKeyUnregisteredError
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageEntityMentionName
import re
import os
import json
from datetime import datetime, timedelta
import datetime
import asyncio
import json
import logging
from dotenv import load_dotenv
load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "SpidertiseSup")

FURL = "https://t.me/SpidertiseSup" 
active_clients = {}
last_reply_time = {}

def load_user_data():
    try:
        with open("config.json", "r") as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = {}  
            return data
    except FileNotFoundError:
        return {"users": {}}  
    except json.JSONDecodeError:
        return {"users": {}}  

def save_user_data(data):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id).strip()
    from main import is_authorized
    if not await is_authorized(user_id):
        await update.message.reply_text(f"🔒 <b>Access Restricted</b>\n\n❌ No active subscription found\n✨ Please contact <a href=\"tg://resolve?domain={ADMIN_USERNAME}\">Admin</a> for access", parse_mode="HTML")
        return

    try:
        message = ' '.join(context.args).split('|')
        keyword = message[0].strip()
        response = message[1].strip().replace('\\n', '\n')

        data = load_user_data()

        if user_id not in data["users"]:
            data["users"][user_id] = {"keywords": {}}

        if "keywords" not in data["users"][user_id]:
            data["users"][user_id]["keywords"] = {}

        data["users"][user_id]["keywords"][keyword] = response
        save_user_data(data)

        await update.message.reply_text(f"Keyword:\n<pre>{keyword}</pre> has been set with the response:\n <pre>{response}</pre>", parse_mode="HTML")

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ *Invalid Format*\n\n📝 Please use:\n`/set_word keyword | response`", parse_mode="Markdown")


async def keyword_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.callback_query.from_user.id).strip()

    from main import is_authorized
    if not await is_authorized(user_id):
        await update.callback_query.edit_message_text(
            f"🔒 <b>Access Restricted</b>\n\n❌ No active subscription found\n✨ Please contact <a href=\"tg://resolve?domain={ADMIN_USERNAME}\">Admin</a> for access",
            parse_mode="HTML"
        )
        return

    # Load user data
    data = load_user_data()
    user_data = data["users"].get(user_id, {})

   
    match_option = user_data.get("match_option", "exact")
    auto_reply_status = "𝙴𝚗𝚊𝚋𝚕𝚎𝚍 ✅" if user_data.get("auto_reply_status", False) else "𝙳𝚒𝚜𝚊𝚋𝚕𝚎𝚍 ❌"
    auto_reply_text = "𝙳𝚒𝚜𝚊𝚋𝚕𝚎 🔴" if user_data.get("auto_reply_status", False) else "𝙴𝚗𝚊𝚋𝚕𝚎 🟢"
    responder_option = user_data.get("responder_option", "𝙿𝙼") 
    save_location = user_data.get("save_location", "chat")

    keyboard = [
            [InlineKeyboardButton("━━━━⊱𝙼𝙰𝚃𝙲𝙷 𝙾𝙿𝚃𝙸𝙾𝙽𝚂⊰━━━", callback_data="pass")],
            [InlineKeyboardButton(f"𝙴𝚡𝚊𝚌𝚝 𝙼𝚊𝚝𝚌𝚑 {'✅' if match_option == 'exact' else '❌'}", callback_data='set_exact')],
            [InlineKeyboardButton(f"𝙿𝚊𝚛𝚝𝚒𝚊𝚕 𝙼𝚊𝚝𝚌𝚑 {'✅' if match_option == 'partial' else '❌'}", callback_data='set_partial')],
            [InlineKeyboardButton(f"𝙲𝚊𝚜𝚎 𝙸𝚗𝚜𝚎𝚗𝚜𝚒𝚝𝚒𝚟𝚎 {'✅' if match_option == 'case_insensitive' else '❌'}", callback_data='set_case_insensitive')],
            [InlineKeyboardButton("━━━━⊱𝚁𝙴𝚂𝙿𝙾𝙽𝚂𝙴 𝚂𝙴𝚃𝚃𝙸𝙽𝙶𝚂⊰━━━", callback_data="pass")],
            [InlineKeyboardButton(f"𝙿𝙼 {'✅' if responder_option == 'PM' else '❌'}", callback_data='set_pm'),
            InlineKeyboardButton(f"𝙶𝙲 {'✅' if responder_option == 'GC' else '❌'}", callback_data='set_gc'),
            InlineKeyboardButton(f"𝙰𝚕𝚕 {'✅' if responder_option == 'All' else '❌'}", callback_data='set_all')],
            [InlineKeyboardButton("━━━━⊱𝙰𝙽𝚃𝙸 𝚅𝙸𝙴𝚆 𝙾𝙽𝙲𝙴 𝚂𝙰𝚅𝙴 𝙻𝙾𝙲𝙰𝚃𝙸𝙾𝙽⊰━━━", callback_data="pass")],
            [InlineKeyboardButton(f"𝚂𝚊𝚟𝚎𝚍 𝙼𝚎𝚜𝚜𝚊𝚐𝚎𝚜 {'✅' if save_location == 'saved' else '❌'}", callback_data='set_saved'),
            InlineKeyboardButton(f"𝙸𝚗-𝙲𝚑𝚊𝚝 {'✅' if save_location == 'chat' else '❌'}", callback_data='set_chat')],
            [InlineKeyboardButton("━━━━⊱𝙶𝚁𝙾𝚄𝙿 𝚃𝙰𝙶𝙶𝙸𝙽𝙶⊰━━━", callback_data="pass")],
            [InlineKeyboardButton("📢 𝙷𝚘𝚠 𝚃𝚘 𝚃𝚊𝚐 𝙰𝚕𝚕", callback_data='how_to_tag')],
            [InlineKeyboardButton(f"{auto_reply_text}", callback_data='toggle_auto_reply')],
            [InlineKeyboardButton("📝 𝙼𝚢 𝙺𝚎𝚢𝚠𝚘𝚛𝚍𝚜", callback_data='words')],
            [InlineKeyboardButton("🔙 𝙱𝚊𝚌𝚔", callback_data='back')]
    ]

    respond_display = {
        'PM': '𝙿𝚛𝚒𝚟𝚊𝚝𝚎 𝙲𝚑𝚊𝚝',
        'GC': '𝙶𝚛𝚘𝚞𝚙𝚜',
        'All': '𝙳𝙼𝚜 & 𝙶𝚛𝚘𝚞𝚙𝚜'
    }.get(responder_option, responder_option)

   
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "⚙️ <b>𝙰𝚄𝚃𝙾-𝚁𝙴𝙿𝙻𝚈 𝚂𝙴𝚃𝚃𝙸𝙽𝙶𝚂 + 𝙰𝙽𝚃𝙸 𝚅𝙸𝙴𝚆 𝙾𝙽𝙲𝙴</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>𝙼𝚊𝚝𝚌𝚑 𝙼𝚘𝚍𝚎:</b> <code>{match_option}</code>\n"
        f"📊 <b>𝚂𝚝𝚊𝚝𝚞𝚜:</b> <code>{auto_reply_status}</code>\n"
        f"🌐 <b>𝚁𝚎𝚜𝚙𝚘𝚗𝚍 𝙸𝚗:</b> <code>{respond_display}</code>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>𝙰𝚗𝚝𝚒 𝚅𝚒𝚎𝚠 𝙾𝚗𝚌𝚎:</b>\n"
        "<code>𝚁𝚎𝚙𝚕𝚢 𝚝𝚘 𝚊𝚗𝚢 𝚟𝚒𝚎𝚠 𝚘𝚗𝚌𝚎 𝚖𝚎𝚍𝚒𝚊 𝚠𝚒𝚝𝚑 /𝚟𝚟</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🔔 <b>𝚃𝚊𝚐 𝙰𝚕𝚕 𝙼𝚎𝚖𝚋𝚎𝚛𝚜:</b>\n"
        "<code>𝚄𝚜𝚎 /𝚝𝚊𝚐 [𝚖𝚎𝚜𝚜𝚊𝚐𝚎] 𝚝𝚘 𝚝𝚊𝚐 𝚊𝚕𝚕 𝚐𝚛𝚘𝚞𝚙 𝚖𝚎𝚖𝚋𝚎𝚛𝚜 𝚊𝚝 𝚘𝚗𝚌𝚎</code>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
async def start_telethon_client(user_id, context=None):
    data = load_user_data()
    user_data = data["users"].get(user_id)

    if not user_data or not user_data.get("auto_reply_status"):
        return

    user_data["client_active"] = True
    save_user_data(data)

    session_file = f"{user_id}.session"
    if not os.path.exists(session_file):
        print(f"Session file for {user_id} does not exist. Ask the user to log in.")
        try:
            if context:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⚠️ <b>Session Error</b>\n\n❌ Your session file is missing\n📝 Please log in again to continue",
                    parse_mode="HTML"
                )
            user_data["auto_reply_status"] = False
            save_user_data(data)
        except Exception as e:
            print(f"Error sending message: {e}")
        return

    api_id = user_data.get("api_id")
    api_hash = user_data.get("api_hash")

    client = TelegramClient(session_file, api_id, api_hash)

    try:

        await client.connect()

        if not await client.is_user_authorized():

            await client.disconnect()
            if os.path.exists(session_file):  
                os.remove(session_file)
            await context.bot.send_message(
                chat_id=user_id,
                text="🔒 *Authorization Failed*\n\n❌ Your session was terminated\n📝 Please log in again to continue",
                parse_mode="Markdown"
            )
            user_data["auto_reply_status"] = False
            save_user_data(data)
            return

        await client.disconnect()
        await asyncio.sleep(3)

        await client.start()
    
    except AuthKeyUnregisteredError as e:
        print(f"Authorization error for user {user_id}: {e}")
        await client.disconnect()
        if os.path.exists(session_file): 
            os.remove(session_file)
        if context:
            await context.bot.send_message(
                chat_id=user_id,
                text="🔒 *Authorization Failed*\n\n❌ Your session was terminated\n📝 Please log in again to continue",
                parse_mode="Markdown"
            )
        user_data["auto_reply_status"] = False
        save_user_data(data)
        return

    except Exception as e:
        print(f"Error starting Telethon client for user {user_id}: {e}")
        user_data["client_active"] = False
        save_user_data(data)
        return

    async def handle_vv_command(event):
        """
        Handles the /vv command to download a specific self-destructing media.
        """
        try:
            user_id = str(event.sender_id)
            data = load_user_data()
            if user_id not in data["users"]:
                data["users"][user_id] = {}
            if "save_location" not in data["users"][user_id]:
                data["users"][user_id]["save_location"] = "chat"  
                save_user_data(data)

            save_location = data["users"][user_id]["save_location"]

            reply = await event.message.get_reply_message()
            if not reply or not reply.media:
                await event.reply("Reply to a message containing self-destructing media to use the /vv command.")
                return

            media = reply.media
            is_self_destruct = (
                isinstance(media, (MessageMediaPhoto, MessageMediaDocument)) and
                getattr(media, "ttl_seconds", None) is not None
            )

            if not is_self_destruct:
                await event.reply("The replied-to message does not contain self-destructing media.")
                return

            logger.info("Downloading self-destructing media targeted by /vv command.")

            try:
                download_path = await reply.download_media()
                logger.info(f"Downloaded self-destructing media to {download_path}")

                caption = f"""
                  🎯 *DOWNLOADED*
                  Self-destruct media saved
                  
                  [Made with ❤️ by FluX𝕏♛]({FURL})
                  """               
                try:
                    if save_location == "saved":
                        await event.client.send_file("me", download_path, caption=caption, parse_mode='Markdown')
                        await event.reply("✅ Media saved to your Saved Messages")
                    else:
                        await event.client.send_file(event.chat_id, download_path, caption=caption, parse_mode='Markdown')

                except FloodWaitError as e:
                    logger.warning(f"FloodWaitError: Waiting for {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                    await event.client.send_file(event.chat_id, download_path, caption=caption, parse_mode='Markdown')
                
                os.remove(download_path)
                logger.info(f"Removed downloaded file from {download_path}")
            except Exception as e:
                logger.error(f"Failed to download media: {e}")
                await event.reply("Failed to download the media.")
        except Exception as e:
            logger.exception(f"Error handling /vv command: {e}")
            await event.reply("An error occurred while processing the /vv command.")

    @client.on(events.NewMessage(pattern='/tag (.+)'))
    async def handle_tag_command(event):
        try:
            sender = await event.get_sender()
            chat = await event.get_input_chat()
            mode = await event.get_chat()

            if not hasattr(mode, 'title'):  
                await event.reply("𝚃𝙷𝙸𝚂 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 𝙲𝙰𝙽 𝙾𝙽𝙻𝚈 𝙱𝙴 𝚄𝚂𝙴𝙳 𝙸𝙽 𝙰 𝙶𝚁𝙾𝚄𝙿 ❌")
                return
            
            # Get the full message text after the command
            full_text = event.message.text
            # Extract everything after "/tag "
            if ' ' in full_text:
                message_text = full_text.split(' ', 1)[1]
            else:
                message_text = ""
            
            # React to the command message
            try:
                from telethon.tl.functions.messages import SendReactionRequest
                from telethon.tl.types import ReactionEmoji
                
                reaction = ReactionEmoji(emoticon='👍')
                await client(SendReactionRequest(
                    peer=chat,
                    msg_id=event.message.id,
                    reaction=[reaction]
                ))
            except Exception as react_error:
                print(f"Couldn't add reaction: {react_error}")
            
            # Inform the user that tagging has started
            status_msg = await client.send_message(sender, "Starting to tag all members...")
            
            # Fetch all participants (excluding bots and the sender)
            all_participants = []
            async for participant in client.iter_participants(chat, aggressive=True):
                if not participant.bot and participant.id != sender.id:
                    all_participants.append(participant)
            
            if not all_participants:
                await client.send_message(sender, "No participants found to tag.")
                return
            
            total_members = len(all_participants)
            await status_msg.edit(f"Found {total_members} members to tag.")
            
            batch_size = 2000
            batches = [all_participants[i:i + batch_size] for i in range(0, len(all_participants), batch_size)]
            
            successful_tags = 0
            skipped_tags = 0
            batch_count = 1
            
            for batch in batches:
                
                mentions = message_text
                
                for user in batch:
                    try:
                        # Add zero-width character AFTER the message text
                        mentions += f'<a href="tg://user?id={user.id}">​</a>'
                        successful_tags += 1
                    except Exception as e:
                        print(f"Couldn't tag user {user.id}: {e}")
                        skipped_tags += 1
                        continue
                
            # Send message with all mentions and HTML formatting
                try:
                    await status_msg.edit(f"Sending batch {batch_count}/{len(batches)}...")
                    sent_message = await client.send_message(
                        chat,
                        mentions,
                        parse_mode='html' 
                    )
                    
                    batch_count += 1
                    await asyncio.sleep(5)  # Small delay between batches
                    
                except Exception as e:
                    print(f"Error sending tag message batch {batch_count}: {e}")
                    await client.send_message(
                        sender,
                        f"Error sending tag message batch {batch_count}: {e}"
                    )
            
            # Final report
            await status_msg.edit(
                f"Tagging complete!\n"
                f"Total members: {total_members}\n"
                f"Successfully tagged: {successful_tags}\n"
                f"Skipped: {skipped_tags}\n"
                f"Sent in {batch_count-1} batches"
            )
            
            await asyncio.sleep(1)
            await event.delete()
            
        except Exception as e:
            print(f"Error in tag command: {e}")
            sender = await event.get_sender()
            await client.send_message(sender, f"Failed to tag members: {str(e)}")

    @client.on(events.NewMessage)
    async def handler(event):
        try:
            chat = await event.get_chat()
            chat_id = chat.id
            chat_name = chat.title if hasattr(chat, 'title') else chat.username or chat_id
            message_text = event.message.message

            if message_text.startswith('/vv') and event.message.is_reply:
                await handle_vv_command(event)
                return

            keywords = user_data.get("keywords", {})
            match_option = user_data.get("match_option", "exact").lower()
            responder_option = user_data.get("responder_option", "PM") 

            for keyword, response in keywords.items():
                if match_option == "exact":
                    pattern = r"^" + re.escape(keyword) + r"$"
                    if re.match(pattern, message_text, re.IGNORECASE):
                        print(f"✨ Exact match found in {chat_name}: {keyword}")
                elif match_option == "partial":
                    pattern = r"\b" + re.escape(keyword) + r"\b"
                    if re.search(pattern, message_text, re.IGNORECASE):
                        print(f"✨ Partial match found in {chat_name}: {keyword}")
                elif match_option == "case_insensitive":
                    if keyword.lower() in message_text.lower():
                        print(f"✨ Case-insensitive match found in {chat_name}: {keyword}")

                if match_option in ["exact", "partial", "case_insensitive"] and (
                    (match_option == "exact" and re.match(pattern, message_text, re.IGNORECASE)) or
                    (match_option == "partial" and re.search(pattern, message_text, re.IGNORECASE)) or
                    (match_option == "case_insensitive" and keyword.lower() in message_text.lower())
                ):
                    if responder_option == "PM" and isinstance(chat, User):
                        if chat_id in last_reply_time and (asyncio.get_event_loop().time() - last_reply_time[chat_id]) < 10:
                            print(f"⏳ Cooldown active in {chat_name}")
                            return

                        await asyncio.sleep(1)

                        if response.startswith("https://t.me/"):
                            await send_message_from_link(client, event, response)
                        else:
                            await event.reply(response)

                        print(f"📤 Replied with: {response}")

                        last_reply_time[chat_id] = asyncio.get_event_loop().time()

                        await asyncio.sleep(10)
                    elif responder_option == "GC" and isinstance(chat, Chat):
                        if chat_id in last_reply_time and (asyncio.get_event_loop().time() - last_reply_time[chat_id]) < 10:
                            print(f"⏳ Cooldown active in {chat_name}")
                            return

                        await asyncio.sleep(1)

                        if response.startswith("https://t.me/"):
                            await send_message_from_link(client, event, response)
                        else:
                            await event.reply(response)

                        print(f"📤 Replied with: {response}")

                        last_reply_time[chat_id] = asyncio.get_event_loop().time()

                        await asyncio.sleep(10)

                    elif responder_option == "All":  # Respond in both PM and GC
                        if chat_id in last_reply_time and (asyncio.get_event_loop().time() - last_reply_time[chat_id]) < 10:
                            print(f"⏳ Cooldown active in {chat_name}")
                            return

                        await asyncio.sleep(1)

                        if response.startswith("https://t.me/"):
                            await send_message_from_link(client, event, response)
                        else:
                            await event.reply(response)

                        print(f"📤 Replied with: {response}")

                        last_reply_time[chat_id] = asyncio.get_event_loop().time()

                        await asyncio.sleep(10)
                    return

        except AuthKeyUnregisteredError as e:
            print(f"Authorization error for user {user_id}: {e}")
            await client.disconnect()
            if os.path.exists(session_file): 
                os.remove(session_file)
            if context:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🔒 *Authorization Failed*\n\n❌ Your session was terminated\n📝 Please log in again to continue",
                    parse_mode="Markdown"
                )
            user_data["auto_reply_status"] = False
            save_user_data(data)
            return

        except Exception as e:
            print(f"Unexpected error while handling message: {e}")
            await client.disconnect()
            if os.path.exists(session_file):
                os.remove(session_file)
            if context:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⚠️ *Unexpected Error*\n\n❌ Your session was terminated unexpectedly\n📝 Please log in again to continue",
                    parse_mode="Markdown"
                )
            user_data["auto_reply_status"] = False
            save_user_data(data)
            return

    try:
        print(f"✅ Telethon client started successfully for user {user_id}")
        user_data["client_active"] = True
        save_user_data(data)

        active_clients[user_id] = client

        asyncio.create_task(client.run_until_disconnected())

    except Exception as e:
        print(f"❌ Error starting Telethon client for user {user_id}: {e}")
        user_data["client_active"] = False
        save_user_data(data)
        
async def send_message_from_link(client, event, link):

    pattern = r"https://t.me/([a-zA-Z0-9_]+)/(\d+)"
    match = re.match(pattern, link)
    if match:
        chat_id = match.group(1)
        message_id = int(match.group(2))
        try:

            message = await client.get_messages(chat_id, ids=message_id)
            if message:

                await client.forward_messages(event.chat_id, message)
            else:
                await event.reply("Message not found.")
        except Exception as e:
            await event.reply(f"Error retrieving message: {e}")
    else:
        await event.reply("Invalid message link.")

async def stop_telethon_client(user_id):
    data = load_user_data()
    user_data = data["users"].get(user_id)

    client = active_clients.get(user_id)

    if client is None:
        print(f"No active Telethon client found for user {user_id}")
        return

    try:
        if client.is_connected():
            print(f"Disconnecting Telethon client for user {user_id}")
            await client.disconnect()
            print(f"Telethon client disconnected for user {user_id}")

        user_data["client_active"] = False
        save_user_data(data)
        del active_clients[user_id]

    except Exception as e:
        print(f"Error stopping Telethon client for user {user_id}: {e}")

    finally:
        if client.is_connected():
            await client.disconnect()
        print(f"Client status after disconnection for user {user_id}: {client.is_connected()}")
