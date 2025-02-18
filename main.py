from telethon.sync import TelegramClient
from telethon import events, types
from telethon.errors.rpcerrorlist import ChatForwardsRestrictedError
from config import *

api_id = int(API_ID)
api_hash = API_HASH

client = TelegramClient(SESSION_DIR, api_id, api_hash,
                        system_version='4.16.30-vxCUSTOM',
                        )
client.start(phone=PHONE, password=PASSWORD)

print('Start Telegram Client')

count = 0


@client.on(events.NewMessage(incoming=True))
async def news_to_chat(event):
    global count
    if isinstance(event.original_update, types.UpdateNewChannelMessage) and event.message.post:
        if event.message.grouped_id is None:
            try:
                await client.forward_messages(entity=int(LENTA_ID),
                                              messages=event.message,
                                              from_peer=event.peer_id)
            except ChatForwardsRestrictedError:
                pass
        else:
            try:
                group_id = event.message.grouped_id
                messages = [mes for mes in await client.get_messages(event.peer_id, limit=10)
                            if mes.grouped_id == group_id]
                count += 1
                if count == len(messages):
                    messages = await client.get_messages(event.peer_id, limit=count)
                    await client.forward_messages(entity=int(LENTA_ID),
                                                  messages=messages,
                                                  from_peer=event.peer_id)
                    count = 0
            except ChatForwardsRestrictedError:
                pass


@client.on(events.NewMessage(incoming=True))
async def mark_archived_dialogs_as_read(event):
    async for dialog in client.iter_dialogs(archived=True):
        if event.message.message == dialog.message.message:
            await client.send_read_acknowledge(entity=await client.get_input_entity(dialog),
                                               max_id=event.message.id,
                                               clear_mentions=True,
                                               clear_reactions=True,
                                               )


@client.on(events.ChatAction())
async def mark_chat_action_as_read(event):
    async for dialog in client.iter_dialogs(archived=True):
        await client.send_read_acknowledge(entity=await client.get_input_entity(dialog),
                                           max_id=event.action_message.id,
                                           clear_mentions=True,
                                           clear_reactions=True,
                                           )


client.run_until_disconnected()
