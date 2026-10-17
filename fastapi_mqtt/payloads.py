"""Pydantic models for message payloads: checks of subscription handlers, validation errors."""

import inspect
import typing
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError

# Message handler arguments, which handlers with a pydantic model parameter get by name
MESSAGE_ARGS = ("client", "topic", "payload", "qos", "properties")


def is_model(hint: Any) -> bool:
    return isinstance(hint, type) and issubclass(hint, BaseModel)


def describe_errors(error: ValidationError) -> str:
    """Validation errors without the input values, which may hold sensitive data."""
    return "; ".join(
        f"{'.'.join(map(str, err['loc'])) or 'payload'}: {err['msg']}"
        for err in error.errors(include_input=False, include_url=False)
    )


def handler_name(handler: Callable[..., Any]) -> str:
    return getattr(handler, "__name__", repr(handler))


def check_no_nested_models(handler: Callable[..., Any], hints: Dict[str, Any]) -> None:
    for param, hint in hints.items():
        if not is_model(hint) and any(is_model(arg) for arg in typing.get_args(hint)):
            raise TypeError(
                f"Handler {handler_name(handler)} parameter {param!r} is typed {hint}, "
                "type it with the pydantic model itself"
            )


def model_spec(
    handler: Callable[..., Any],
) -> Optional[Tuple[str, Type[BaseModel], List[str]]]:
    """
    Check a subscription handler when it is registered.

    Returns None for a handler without a parameter typed as a pydantic model,
    or (model parameter, model, other message arguments it takes by name).
    Raises TypeError for a handler that can't be called with the messages.
    """
    name = handler_name(handler)
    try:
        hints = typing.get_type_hints(handler)
    except Exception:  # noqa: BLE001 (handlers without readable annotations)
        hints = {}
    try:
        signature = inspect.signature(handler)
    except (TypeError, ValueError):
        return None  # can't be inspected, called as usual
    hints = {param: hint for param, hint in hints.items() if param in signature.parameters}
    check_no_nested_models(handler, hints)

    model_params = [param for param, hint in hints.items() if is_model(hint)]
    if not model_params:
        try:
            signature.bind(*MESSAGE_ARGS)
        except TypeError:
            raise TypeError(
                f"Handler {name} must accept the arguments {list(MESSAGE_ARGS)}, "
                "or have a parameter typed with a pydantic model"
            ) from None
        return None
    if len(model_params) > 1:
        raise TypeError(
            f"Handler {name} has more than one pydantic model parameter: {model_params}"
        )

    model_param = model_params[0]
    others = [param for param in signature.parameters if param != model_param]
    unknown = [
        param
        for param in others
        if param not in MESSAGE_ARGS
        and signature.parameters[param].default is inspect.Parameter.empty
    ]
    if unknown:
        raise TypeError(
            f"Handler {name} has unknown parameters {unknown}, expected any of {list(MESSAGE_ARGS)}"
        )
    args = [param for param in others if param in MESSAGE_ARGS]
    try:
        signature.bind(**dict.fromkeys([model_param, *args]))
    except TypeError as exc:
        raise TypeError(f"Handler {name} can't be called with keyword arguments: {exc}") from None
    return model_param, hints[model_param], args
