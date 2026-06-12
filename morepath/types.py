from __future__ import annotations

from collections.abc import Callable, Iterable
from os import PathLike
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    ParamSpec,
    Protocol,
    TypeAlias,
)

from webob import Response as BaseResponse

from .app import App
from .converter import Converter, ListConverter
from .request import Request

if TYPE_CHECKING:
    from typing_extensions import TypeVar

    AppT = TypeVar("AppT", bound=App, default=Any)
    RequestT = TypeVar("RequestT", bound=Request[Any], default=Any)
    TweenT = TypeVar("TweenT", bound="Tween", default=Any)
else:
    from typing import TypeVar

    AppT = TypeVar("AppT", bound=App)
    RequestT = TypeVar("RequestT", bound=Request[Any])
    TweenT = TypeVar("TweenT", bound="Tween")


_T = TypeVar("_T")
_KT_co = TypeVar("_KT_co", covariant=True)
_VT_co = TypeVar("_VT_co", covariant=True)
_P = ParamSpec("_P")


class SupportsItems(Protocol[_KT_co, _VT_co]):
    def items(self) -> Iterable[tuple[_KT_co, _VT_co]]: ...


class StartResponse(Protocol):
    def __call__(
        self,
        status: str,
        headers: list[tuple[str, str]],
        exc_info: OptExcInfo | None = ...,
        /,
    ) -> Callable[[bytes], object]: ...


# NOTE: We would like these to have an upper bound of App/Request
#       but that's not currently possible to express
AnyApp: TypeAlias = Any
AnyRequest: TypeAlias = Any
AnyConverter: TypeAlias = Converter[Any] | ListConverter[Any]
Tween: TypeAlias = Callable[[RequestT], BaseResponse]
TweenFactory: TypeAlias = Callable[[AppT, TweenT], Tween]
WSGIEnvironment: TypeAlias = dict[str, Any]
WSGIApplication: TypeAlias = Callable[
    [WSGIEnvironment, StartResponse], Iterable[bytes]
]
ExcInfo: TypeAlias = tuple[type[BaseException], BaseException, TracebackType]
OptExcInfo: TypeAlias = ExcInfo | tuple[None, None, None]
StrPath: TypeAlias = PathLike[str] | str
GetStrPath: TypeAlias = Callable[[], StrPath]
MaybeTakesApp: TypeAlias = (
    Callable[Concatenate[AnyApp, _P], _T] | Callable[_P, _T]
)
Render: TypeAlias = Callable[[Any, AnyRequest], BaseResponse]
GetRender: TypeAlias = Callable[[Any, str, Render], Render]
