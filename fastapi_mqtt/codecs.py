from typing import Any, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

M = TypeVar("M", bound=BaseModel)


def decode_error(
    model: Type[BaseModel], codec: str, payload: bytes, exc: Exception
) -> ValidationError:
    """A payload that can't be decoded, as ValidationError, like invalid JSON."""
    return ValidationError.from_exception_data(
        model.__name__,
        [
            InitErrorDetails(
                type=PydanticCustomError(
                    "payload_decode",
                    "Invalid {codec} payload: {reason}",
                    {"codec": codec, "reason": str(exc) or type(exc).__name__},
                ),
                loc=(),
                input=payload,
            )
        ],
    )


class Codec:
    """
    Base codec. Subclass implement `loads` and `dumps` (bytes <-> Python data),
    and pydantic validates the data, or override `decode` and `encode` directly.
    """

    name = "codec"

    def loads(self, payload: bytes) -> Any:
        raise NotImplementedError

    def dumps(self, data: Any) -> bytes:
        raise NotImplementedError

    def decode(self, model: Type[M], payload: bytes) -> M:
        try:
            data = self.loads(payload)
        except Exception as exc:
            raise decode_error(model, self.name, payload, exc) from exc
        return model.model_validate(data)

    def encode(self, item: BaseModel) -> Union[bytes, str]:
        return self.dumps(item.model_dump(mode="json"))


class JSONCodec(Codec):
    """Default codec, same behaviour as before codecs existed."""

    name = "json"

    def decode(self, model: Type[M], payload: bytes) -> M:
        return model.model_validate_json(payload)

    def encode(self, item: BaseModel) -> str:
        return item.model_dump_json()


class MsgPackCodec(Codec):
    """MsgPack"""

    name = "msgpack"

    def __init__(self):
        try:
            import msgpack
        except ImportError as exc:
            raise ImportError(
                "MsgPackCodec needs msgpack: pip install fastapi-mqtt[msgpack]"
            ) from exc
        self._msgpack = msgpack

    def loads(self, payload: bytes) -> Any:
        return self._msgpack.unpackb(payload, raw=False)

    def dumps(self, data: Any) -> bytes:
        return self._msgpack.packb(data, use_bin_type=True)


class BSONCodec(Codec):
    name = "bson"

    def __init__(self):
        try:
            import bson
        except ImportError as exc:
            raise ImportError("BSONCodec needs pymongo: pip install fastapi-mqtt[bson]") from exc
        if not hasattr(bson, "encode"):
            raise ImportError(
                "BSONCodec needs the bson moodule from pymongo, "
                "the standalone 'bson' package from PyPI is not compatible"
            )
        self._bson = bson

    def loads(self, payload: bytes) -> Any:
        return self._bson.decode(payload)

    def dumps(self, data: Any) -> bytes:
        return self._bson.encode(data)
