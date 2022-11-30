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

        self.virtual_roles = self.VirtualRoles(meta, self.conn)
        self.virtual_role_emojis = self.VirtualRoleEmojis(meta, self.conn)
        self.virtual_reaction_messages = self.VirtualReactionMessages(meta, self.conn)
        self.virtual_reaction_roles = self.VirtualReactionRoles(meta, self.conn)
        # self.virtual_role_collection = self.VirtualRoleCollection(meta, self.conn)

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

    class VirtualRoles(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_roles = Table(
                'virtual_roles', meta,
                Column('id', Integer, primary_key=True),
                Column('uuid', String),
                Column('role_name', String)
            )

            super().__init__(self.virtual_roles, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_role_id(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_role_id(self, r_id: str):
            sel = self.table.select().where(self.table.columns.uuid == r_id)
            return list(self.conn.execute(sel))

        def fetch_by_role_id(self, r_id: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_role_id(r_id), val_pos)

        def insert(self, uuid: str, role_name: str):
            self.insert_([{'uuid': uuid, 'role_name': role_name}])

        def set(self, uuid: str, role_name: str) -> Any:
            val = self.fetch_by_role_id(uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.uuid == uuid).values(
                    role_name=role_name)
                self.conn.execute(rep)
                return role_name
            else:
                self.insert(uuid, role_name)
                return role_name

    class VirtualRoleEmojis(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_role_emojis = Table(
                'virtual_role_emojis', meta,
                Column('id', Integer, primary_key=True),
                Column('uuid', String),
                Column('emoji', String)
            )

            super().__init__(self.virtual_role_emojis, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_role_id(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_role_id(self, r_id: str):
            sel = self.table.select().where(self.table.columns.uuid == r_id)
            return list(self.conn.execute(sel))

        def fetch_by_role_id(self, r_id: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_role_id(r_id), val_pos)

        def insert(self, uuid: str, emoji: str):
            self.insert_([{'uuid': uuid, 'emoji': emoji}])

        def set(self, uuid: str, emoji: str) -> Any:
            val = self.fetch_by_role_id(uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.uuid == uuid).values(
                    emoji=emoji)
                self.conn.execute(rep)
                return emoji
            else:
                self.insert(uuid, emoji)
                return emoji

    class VirtualReactionMessages(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_reaction_messages = Table(
                'virtual_reaction_messages', meta,
                Column('id', Integer, primary_key=True),
                Column('msg_uuid', String),
                Column('message_id', Integer)
            )

            super().__init__(self.virtual_reaction_messages, self.conn)

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

        def fetch_by_msg_uuid(self, msg_uuid: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_msg_uuid(msg_uuid), val_pos)

        def insert(self, msg_uuid: str, message_id: str):
            self.insert_([{'msg_uuid': msg_uuid, 'message_id': message_id}])

        def set(self, msg_uuid: str, message_id: str) -> Any:
            val = self.fetch_by_msg_uuid(msg_uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.msg_uuid == msg_uuid).values(
                    message_id=message_id)
                self.conn.execute(rep)
                return message_id
            else:
                self.insert(msg_uuid, message_id)
                return message_id

    class VirtualReactionRoles(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_reaction_roles = Table(
                'virtual_reaction_roles', meta,
                Column('id', Integer, primary_key=True),
                Column('msg_uuid', String),
                Column('role_uuid', String)
            )

            super().__init__(self.virtual_reaction_roles, self.conn)

        def delete(self, uuid: str):
            val = self.fetch_by_msg_uuid(uuid)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.uuid == uuid)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_msg_uuid(self, msg_uuid: str):
            sel = self.table.select().where(self.table.columns.uuid == msg_uuid)
            return list(self.conn.execute(sel))

        def fetch_by_msg_uuid(self, msg_uuid: str, val_pos=1):
            return ValueHelper.list_tuple_value(self.fetch_all_by_msg_uuid(msg_uuid), val_pos)

        def insert(self, msg_uuid: str, role_uuid: str):
            self.insert_([{'msg_uuid': msg_uuid, 'role_uuid': role_uuid}])

        def set(self, msg_uuid: str, role_uuid: str) -> Any:
            val = self.fetch_by_msg_uuid(msg_uuid)
            if val is not None:
                rep = self.table.update().where(self.table.columns.msg_uuid == msg_uuid).values(
                    role_uuid=role_uuid)
                self.conn.execute(rep)
                return role_uuid
            else:
                self.insert(msg_uuid, role_uuid)
                return role_uuid

    class VirtualRoleCollection(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_role_collection = Table(
                'virtual_role_collection', meta,
                Column('id', Integer, primary_key=True),
                Column('user_id', Integer),
                Column('uuid', String)
            )

            super().__init__(self.virtual_role_collection, self.conn)

        def delete(self, user_id: int):
            val = self.fetch_by_role_id(user_id)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.user_id == user_id)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_user_id(self, u_id: int):
            sel = self.table.select().where(self.table.columns.user_id == u_id)
            return list(self.conn.execute(sel))

        def fetch_by_role_id(self, m_id: int, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_user_id(m_id), val_pos)

        def insert(self, user_id: int, uuid: str):
            self.insert_([{'user_id': user_id, 'uuid': uuid}])
