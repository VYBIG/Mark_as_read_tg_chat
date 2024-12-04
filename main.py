from telethon.sync import TelegramClient
from telethon import events, types
from telethon.tl.functions.messages import ReadHistoryRequest
from config import *
api_id = int(API_ID)
api_hash = API_HASH

client = TelegramClient(SESSION_DIR, api_id, api_hash,
                        system_version='4.16.30-vxCUSTOM',
                        )
client.start(phone=PHONE)

print('Start to read message from Archive')



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
