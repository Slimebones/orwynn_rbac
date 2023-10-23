from typing import Any
from antievil import NotFoundError
from orwynn.base import Module, Service
from orwynn.mongo import Document, DocumentSearch, MongoUtils


class MongoStateFlag(Document):
    key: str
    value: bool


class MongoStateFlagSearch(DocumentSearch):
    keys: list[str] | None = None
    values: list[bool] | None = None


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
            query["key"] = {
                "$in": search.keys
            }
        if search.values:
            query["value"] = {
                "$in": search.values
            }

        return MongoUtils.process_query(
            query,
            search,
            MongoStateFlag
        )

    def set(
        self,
        key: str,
        value: bool
    ) -> MongoStateFlag:
        """
        Sets new value for a key.

        If the key does not exist, create a new state flag with given value.
        """
        flag: MongoStateFlag

        try:
            flag = self.get(MongoStateFlagSearch(
                keys=[key]
            ))[0]
        except NotFoundError:
            flag = MongoStateFlag(key=key, value=value).create()
        else:
            flag = flag.update(set={"value": value})

        return flag


module = Module(
    Providers=[MongoStateFlagService]
)
