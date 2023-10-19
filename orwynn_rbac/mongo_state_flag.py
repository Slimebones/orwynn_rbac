from typing import Any
from antievil import NotFoundError
from orwynn.base import Module, Service
from orwynn.mongo import Document, DocumentSearch, MongoUtils
from orwynn.mongo.mongo import DatabaseEntityNotFoundError
from orwynn.utils.klass import Static


class MongoStateFlag(Document):
    key: str
    flag: bool


class MongoStateFlagSearch(DocumentSearch):
    keys: list[str]
    flags: list[bool]


class MongoStateFlagService(Service):
    def get(
        self,
        search: MongoStateFlagSearch
    ) -> list[MongoStateFlag]:
        query: dict[str, Any] = {}

        if search.ids:
            query["id"] = {
                "$in": search.ids
            }
        if search.keys:
            query["keys"] = {
                "$in": search.keys
            }
        if search.flags:
            query["keys"] = {
                "$in": search.flags
            }

        return MongoUtils.process_query(
            query,
            search,
            MongoStateFlag
        )


module = Module(
    Providers=[MongoStateFlagService]
)
