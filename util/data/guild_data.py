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
        # self.virtual_reaction_roles = self.VirtualReactionRoles(meta, self.conn)
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
                Column('unique_identifier', String),
                Column('role_name', String)
            )

            super().__init__(self.virtual_roles, self.conn)

        def delete(self, unique_identifier: str):
            val = self.fetch_by_role_id(unique_identifier)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.unique_identifier == unique_identifier)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_role_id(self, r_id: str):
            sel = self.table.select().where(self.table.columns.unique_identifier == r_id)
            return list(self.conn.execute(sel))

        def fetch_by_role_id(self, r_id: str, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_role_id(r_id), val_pos)

        def insert(self, unique_identifier: str, role_name: str):
            self.insert_([{'unique_identifier': unique_identifier, 'role_name': role_name}])

        def set(self, unique_identifier: str, role_name: str) -> Any:
            val = self.fetch_by_role_id(unique_identifier)
            if val is not None:
                rep = self.table.update().where(self.table.columns.unique_identifier == unique_identifier).values(
                    role_name=role_name)
                self.conn.execute(rep)
                return role_name
            else:
                self.insert(unique_identifier, role_name)
                return role_name

    class VirtualReactionRoles(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_reaction_roles = Table(
                'virtual_reaction_roles', meta,
                Column('id', Integer, primary_key=True),
                Column('message_id', Integer),
                Column('unique_identifier', String),
                Column('emoji', String)
            )

            super().__init__(self.virtual_reaction_roles, self.conn)

        def delete(self, message_id: int):
            val = self.fetch_by_message_id(message_id)
            if val is not None:
                rep = self.table.delete().where(self.table.columns.message_id == message_id)
                self.conn.execute(rep)
                return True
            else:
                return False

        def fetch_all_by_message_id(self, m_id: int):
            sel = self.table.select().where(self.table.columns.message_id == m_id)
            return list(self.conn.execute(sel))

        def fetch_by_message_id(self, m_id: int, val_pos=2):
            return ValueHelper.list_tuple_value(self.fetch_all_by_message_id(m_id), val_pos)

        def insert(self, message_id: int, role_id: int, emoji: str):
            self.insert_([{'message_id': message_id, 'role_id': role_id, 'emoji': emoji}])

    class VirtualRoleCollection(TableHelper):
        def __init__(self, meta, conn):
            self.conn = conn

            self.virtual_role_collection = Table(
                'virtual_role_collection', meta,
                Column('id', Integer, primary_key=True),
                Column('user_id', Integer),
                Column('unique_identifier', String)
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

        def insert(self, user_id: int, unique_identifier: str):
            self.insert_([{'user_id': user_id, 'unique_identifier': unique_identifier}])
