from telethon.sync import TelegramClient
from telethon import events, types

# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
api_id = 27326624
api_hash = '261863acefacdc9d7ab5426cecd4631b'

client = TelegramClient('/root/read_messages/read_archived_message/VY_BIG_Client.session', api_id, api_hash,
                        system_version='4.16.30-vxCUSTOM',
                        )
client.start(phone='+79619062680')

print('Start to read message from Archive')


@client.on(events.ChatAction())
@client.on(events.NewMessage(incoming=True))
async def mark_archived_dialogs_as_read(event):
    async for dialog in client.iter_dialogs(archived=True):
        if event.message.id == dialog.message.id:
            # print(f'Чат {dialog.name} в Архиве')
            if isinstance(event.peer_id, types.PeerChat):
                # print(f'Чат {dialog.name} это Группа')
                await client.send_read_acknowledge(entity=event.message.peer_id.chat_id,
                                                   # message=event.message.message,
                                                   # max_id = 0,
                                                   max_id=event.message.id,
                                                   clear_mentions=True,
                                                   clear_reactions=True,
                                                   )
            elif isinstance(event.peer_id, types.PeerChannel):
                # print(f'Чат {dialog.name} это Канал')
                await client.send_read_acknowledge(entity=event.message.peer_id.channel_id,
                                                   # message=event.message.message,
                                                   # max_id=0,
                                                   max_id=event.message.id,
                                                   clear_mentions=True,
                                                   clear_reactions=True,
                                                   )


client.run_until_disconnected()
