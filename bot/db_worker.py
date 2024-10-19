import sqlite3


class DBWorker:
    _init_table_query = """
        DROP TABLE IF EXISTS users;
        CREATE TABLE users (
            id INTEGER PRIMARY KEY ASC,
            chat_id TEXT UNIQUE,
            log_level TEXT
        );
    """
    _get_table_query = """
        SELECT name FROM sqlite_master WHERE type='table';
    """
    _get_chats_query = """
        SELECT chat_id, log_level FROM users
    """
    _insert_chat_query = """
        INSERT INTO users VALUES (NULL, ?, ?)
    """
    _delete_chat_query = """
        DELETE FROM users WHERE chat_id = ?
    """
    _update_log_level_query = """
        UPDATE users
        SET log_level = ?
        WHERE chat_id = ?
    """

    def __init__(self, path: str) -> None:
        """
        Open connection and create cursor to work with local database (create new if not exist)
        """
        self._path = path
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

        tables = self.cursor.execute(self._get_table_query).fetchall()
        if ("users",) not in tables:
            self.cursor.executescript(self._init_table_query)
            self.connection.commit()

    def get_chats(self) -> list[tuple[str, str]]:
        """
        Get list of chats
        """
        return self.cursor.execute(self._get_chats_query).fetchall()

    def insert_chat(self, chat_id: str, log_level: str = "ERROR") -> None:
        """
        Insert new chat into database
        """
        if chat_id not in [i[0] for i in self.get_chats()]:
            self.cursor.execute(self._insert_chat_query, [chat_id, log_level])
            self.connection.commit()

    def delete_chat(self, chat_id: str) -> None:
        """
        Remove chat from database
        """
        self.cursor.execute(self._delete_chat_query, [chat_id])
        self.connection.commit()

    def set_log_level(self, chat_id: str, log_level: str) -> None:
        """
        Set log level for chat
        """
        self.cursor.execute(self._update_log_level_query, [log_level, chat_id])
        self.connection.commit()
