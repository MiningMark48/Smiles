from typing import Any

from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData, Boolean

from util.data.table_helper import TableHelper
from util.data.value_helper import ValueHelper


class GuildData:
    def __init__(self, guild_id):
        self.guild_id = guild_id

        engine = create_engine(f'sqlite:///data/guild_{self.guild_id}.db', echo=False)
        meta = MetaData()
        self.conn = engine.connect()

        self.booleans = self.Booleans(meta, self.conn)
        self.disabled_commands = self.DisabledCommands(meta, self.conn)
        self.strings = self.Strings(meta, self.conn)
        self.tags = self.Tags(meta, self.conn)
        self.custom_commands = self.CustomCommands(meta, self.conn)

        self.collectibles = self.Collectibles(meta, self.conn)
        self.collectible_emojis = self.CollectibleEmoji(meta, self.conn)
        self.collectible_messages = self.CollectibleMessages(meta, self.conn)
        self.collectible_reactions = self.CollectibleReactions(meta, self.conn)
        self.collectible_collection = self.CollectiblesCollection(meta, self.conn)

        meta.create_all(engine)

    class Booleans(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.booleans = Table(
                'booleans', meta,
                Column('id', Integer, primary_key=True),
                Column('name', String, unique=True),
                Column('value', Boolean)
            )

            super().__init__(self.booleans, self.conn)

        def insert(self, name: str, value: bool):
            self.insert_([{'name': name, 'value': value}])

    class DisabledCommands(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.disabled_commands = Table(
                'disabled_commands', meta,
                Column('id', Integer, primary_key=True),
                Column('name', String, unique=True)
            )

            super().__init__(self.disabled_commands, self.conn)

        def delete(self, name: str):
            val = self.fetch_by_name(name, 1)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.name == name)
                self.conn.execute(rep)
                return True
            else:
                return False

        def insert(self, name: str):
            self.insert_([{'name': name}])

    class Strings(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.strings = Table(
                'strings', meta,
                Column('id', Integer, primary_key=True),
                Column('name', String, unique=True),
                Column('value', String)
            )

            super().__init__(self.strings, self.conn)

        def insert(self, name: str, value: str):
            self.insert_([{'name': name, 'value': value}])

    class Tags(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.tags = Table(
                'tags', meta,
                Column('id', Integer, primary_key=True),
                Column('name', String, unique=True),
                Column('value', String)
            )

            super().__init__(self.tags, self.conn)

        def insert(self, name: str, value: str):
            self.insert_([{'name': name, 'value': value}])

    class CustomCommands(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.custom_commands = Table(
                'custom_commands', meta,
                Column('id', Integer, primary_key=True),
                Column('name', String, unique=True),
                Column('value', String)
            )

            super().__init__(self.custom_commands, self.conn)

        def insert(self, name: str, value: str):
            self.insert_([{'name': name, 'value': value}])

    class Collectibles(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.collectibles = Table(
                'collectibles', meta,
                Column('id', Integer, primary_key=True),
                Column('uuid', String),
                Column('display_name', String)
            )

            super().__init__(self.collectibles, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_id(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_id(self, uuid: str):
            sel = self.table.select().where(self.table.columns.uuid == uuid)
            return list(self.conn.execute(sel))

        def fetch_by_id(self, uuid: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_id(uuid), val_pos)

        def insert(self, uuid: str, display_name: str):
            self.insert_([{'uuid': uuid, 'display_name': display_name}])

        def set(self, uuid: str, display_name: str) -> Any:
            val = self.fetch_by_id(uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.uuid == uuid).values(
                    display_name=display_name)
                self.conn.execute(rep)
                return display_name
            else:
                self.insert(uuid, display_name)
                return display_name

    class CollectibleEmoji(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.collectible_emoji = Table(
                'collectible_emoji', meta,
                Column('id', Integer, primary_key=True),
                Column('uuid', String),
                Column('emoji', String)
            )

            super().__init__(self.collectible_emoji, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_id(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_id(self, uuid: str):
            sel = self.table.select().where(self.table.columns.uuid == uuid)
            return list(self.conn.execute(sel))

        def fetch_by_id(self, uuid: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_id(uuid), val_pos)

        def fetch_all_by_emoji(self, emoji: str):
            sel = self.table.select().where(self.table.columns.emoji == emoji)
            return list(self.conn.execute(sel))

        def fetch_by_emoji(self, emoji: str, val_pos=3):
            return ValueHelper.list_tuple_value(self.fetch_all_by_emoji(emoji), val_pos)

        def insert(self, uuid: str, emoji: str):
            self.insert_([{'uuid': uuid, 'emoji': emoji}])

        def set(self, uuid: str, emoji: str) -> Any:
            val = self.fetch_by_id(uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.uuid == uuid).values(
                    emoji=emoji)
                self.conn.execute(rep)
                return emoji
            else:
                self.insert(uuid, emoji)
                return emoji

    class CollectibleMessages(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.collectible_messages = Table(
                'collectible_messages', meta,
                Column('id', Integer, primary_key=True),
                Column('uuid', String),
                Column('message_id', String)
            )

            super().__init__(self.collectible_messages, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_msg_uuid(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_msg_uuid(self, uuid: str):
            sel = self.table.select().where(self.table.columns.uuid == uuid)
            return list(self.conn.execute(sel))

        def fetch_by_msg_uuid(self, uuid: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_msg_uuid(uuid), val_pos)

        def fetch_all_by_msg_id(self, msg_id: str):
            sel = self.table.select().where(self.table.columns.message_id == msg_id)
            return list(self.conn.execute(sel))

        def fetch_by_msg_id(self, msg_id: str, val_pos=1):
            return ValueHelper.list_tuple_value(self.fetch_all_by_msg_id(msg_id), val_pos)

        def insert(self, uuid: str, message_id: str):
            self.insert_([{'uuid': uuid, 'message_id': message_id}])

        def set(self, uuid: str, message_id: str) -> Any:
            val = self.fetch_by_msg_uuid(uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.uuid == uuid).values(
                    message_id=message_id)
                self.conn.execute(rep)
                return message_id
            else:
                self.insert(uuid, message_id)
                return message_id

    class CollectibleReactions(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.collectible_reactions = Table(
                'collectible_reactions', meta,
                Column('id', Integer, primary_key=True),
                Column('msg_uuid', String),
                Column('collect_uuid', String)
            )

            super().__init__(self.collectible_reactions, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_msg_uuid(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.msg_uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_msg_uuid(self, msg_uuid: str):
            sel = self.table.select().where(self.table.columns.msg_uuid == msg_uuid)
            return list(self.conn.execute(sel))

        def fetch_by_msg_uuid(self, msg_uuid: str, val_pos=1):
            return ValueHelper.list_tuple_value(self.fetch_all_by_msg_uuid(msg_uuid), val_pos)

        def fetch_all_by_collect_id(self, collect_id: str):
            sel = self.table.select().where(self.table.columns.collect_uuid == collect_id)
            return list(self.conn.execute(sel))

        def fetch_by_collect_id(self, collect_id: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_collect_id(collect_id), val_pos)

        def insert(self, msg_uuid: str, collect_uuid: str):
            self.insert_([{'msg_uuid': msg_uuid, 'collect_uuid': collect_uuid}])

        def set(self, msg_uuid: str, collect_uuid: str) -> Any:
            val = self.fetch_by_msg_uuid(msg_uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.msg_uuid == msg_uuid).values(
                    collect_uuid=collect_uuid)
                self.conn.execute(rep)
                return collect_uuid
            else:
                self.insert(msg_uuid, collect_uuid)
                return collect_uuid

        def delete_where(self, msg_uuid: str, collect_uuid: str) -> Any:
            val = self.fetch_by_msg_uuid(msg_uuid)
            if val is not None:
                rep = self.table.delete().where(
                    (self.table.columns.msg_uuid == msg_uuid) & (self.table.columns.collect_uuid == collect_uuid))
                self.conn.execute(rep)
                return True
            else:
                return False

        def delete_where_collect_id(self, uuid: str) -> Any:
            val = ValueHelper.list_tuple_value(
                list(self.conn.execute(self.table.select().where(self.table.columns.collect_uuid == uuid))), 2)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.collect_uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

    class CollectiblesCollection(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.collectibles_collection = Table(
                'collectibles_collection', meta,
                Column('id', Integer, primary_key=True),
                Column('user_id', String),
                Column('uuid', String)
            )

            super().__init__(self.collectibles_collection, self.conn)

        def delete(self, user_id: str):
            val = self.fetch_by_user_id(user_id)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.user_id == user_id)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_user_id(self, u_id: str):
            sel = self.table.select().where(self.table.columns.user_id == u_id)
            return list(self.conn.execute(sel))

        def fetch_by_user_id(self, u_id: str, val_pos=1):
            return ValueHelper.list_tuple_value(self.fetch_all_by_user_id(u_id), val_pos)

        def fetch_all_by_collect_id(self, collect_id: str):
            sel = self.table.select().where(self.table.columns.uuid == collect_id)
            return list(self.conn.execute(sel))

        def fetch_by_collect_id(self, collect_id: str, val_pos=1):
            return ValueHelper.list_tuple_value(self.fetch_all_by_user_id(collect_id), val_pos)

        def fetch_by_user_id_where(self, user_id: str, collect_uuid: str):
            val = self.fetch_by_user_id(user_id)
            if val is not None:
                rep = self.table.select().where(
                    (self.table.columns.user_id == user_id) & (self.table.columns.uuid == collect_uuid))
                return list(self.conn.execute(rep))
            else:
                return None

        def insert(self, user_id: str, uuid: str):
            self.insert_([{'user_id': user_id, 'uuid': uuid}])

        def delete_where(self, user_id: str, uuid: str) -> Any:
            val = self.fetch_by_user_id(user_id)
            if val is not None:
                rep = self.table.delete().where(
                    (self.table.columns.user_id == user_id) & (self.table.columns.uuid == uuid))
                self.conn.execute(rep)
                return True
            else:
                return False

        def delete_where_uuid(self, uuid: str) -> Any:
            val = ValueHelper.list_tuple_value(
                list(self.conn.execute(self.table.select().where(self.table.columns.uuid == uuid))), 2)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False
