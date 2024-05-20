from telethon.sync import TelegramClient
from telethon import events, types


api_id = 27326624
api_hash = '261863acefacdc9d7ab5426cecd4631b'

client = TelegramClient('/root/read_messages/read_archived_message/VY_BIG_Client.session', api_id, api_hash,
                        system_version='4.16.30-vxCUSTOM',
                        )
client.start(phone='+79619062680')

print('Start to read message from Archive')


@client.on(events.ChatAction())
async def mark_chat_action_as_read(event):
    if isinstance(event.action_message.peer_id, types.PeerChat):
        await client.send_read_acknowledge(entity=event.action_message.peer_id.chat_id,
                                           max_id=event.action_message.id,
                                           clear_mentions=True,
                                           clear_reactions=True,
                                           )
    elif isinstance(event.action_message.peer_id, types.PeerChannel):
        await client.send_read_acknowledge(entity=event.action_message.peer_id.channel_id,
                                           max_id=event.action_message.id,
                                           clear_mentions=True,
                                           clear_reactions=True,
                                           )


@client.on(events.NewMessage(incoming=True))
async def mark_archived_dialogs_as_read(event):
    async for dialog in client.iter_dialogs(archived=True):
        if event.message.message == dialog.message.message:
            if isinstance(event.peer_id, types.PeerChat):
                await client.send_read_acknowledge(entity=await client.get_entity(dialog.name),
                                                   max_id=event.message.id,
                                                   clear_mentions=True,
                                                   clear_reactions=True,
                                                   )
            elif isinstance(event.peer_id, types.PeerChannel):
                entity = await client.get_entity(event.message.peer_id.channel_id)
                if entity.megagroup:
                    pass
                else:
                    await client.send_read_acknowledge(entity=await client.get_entity(dialog.name),
                                                       max_id=event.message.id,
                                                       clear_mentions=True,
                                                       clear_reactions=True,
                                                       )

client.run_until_disconnected()
