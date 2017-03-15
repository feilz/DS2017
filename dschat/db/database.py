
import os

from sqlalchemy.engine import create_engine


class Database():
    def __init__(self, path="./dschat_database.db", mode="sqlite"):
        self.path = path

        schema = open("dschat/db/DS17.schema", "r").read()

        if mode == "sqlite":

            if not os.path.isfile(path):
                import sqlite3
                conn = sqlite3.connect(self.path)
                conn.executescript(schema)
                conn.commit()
                conn.close()

            self.engine = create_engine("sqlite:///%s" % self.path, echo=True)

        elif mode == "postgresql":
            pass

        self.conn = self.engine.connect()

    def user_exists(self, user):
        return self.get_user_id(user)

    def insert_user(self, **kwargs):
        try:
            self.conn.execute("INSERT INTO users VALUES (NULL, '{user}'); """.format(**kwargs))
        except sqlite3.IntegrityError:
            # TODO
            # User is already in database
            # Handle this from Flask side. I.e. query first for a user of same name
            return False

        return True

    def get_user_id(self, user):
        results = self.conn.execute("SELECT id FROM users WHERE name = '{0}';".format(user))
        
        try:
            user_id = results.first()[0]
        except TypeError:
            # TODO
            # Handle cases where user is not in database
            return

        return user_id

    def insert_message(self, **kwargs):
        kwargs["user"] = self.get_user_id(kwargs["user"])

        self.conn.execute("INSERT INTO messages VALUES (NULL, {user}, {ts}, '{message}', '{room}');".format(**kwargs))

    def close(self):
        self.conn.close()
