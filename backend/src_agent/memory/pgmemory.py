from langgraph.checkpoint.postgres import PostgresSaver


class PGMemory:
    def __init__(self, connection_string: str):
        self.db_uri = connection_string
        self.checkpointer = self._get_checkpointer()

    def _get_checkpointer(self):
        return PostgresSaver.from_conn_string(self.db_uri)
