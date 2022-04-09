from datetime import (
    datetime
)
from typing import (
    Callable,
    List,
    Any,
    Type,
    TypeVar,
    Generic,
    Tuple,
    Optional,
)


from credmark.dto import (
    GenericDTO,
    DTOField,
    IterableListGenericDTO,
    PrivateAttr,
)

# pylint:disable=locally-disabled,too-many-instance-attributes

P = TypeVar('P')  # Plan return type
C = TypeVar('C')  # Chef return type


class Recipe(GenericDTO, Generic[C, P]):
    cache_keywords: List[Any]  # Unique keywords in Plan's Cache
    target_key: str  # Unique key in Market
    method: str
    input: dict
    post_proc: Callable[[Any, C], P]
    error_handle: Callable[[Any, Exception], Tuple[str, P]]
    chef_return_type: Type[C]
    plan_return_type: Type[P]


class RiskObject:
    @ property
    def name_id(self):
        return f'{self.__class__.__name__}({hex(id(self))})'


DTOCLS = TypeVar('DTOCLS')


class BlockData(IterableListGenericDTO[DTOCLS], Generic[DTOCLS]):
    data: List[Tuple[int, DTOCLS]] = \
        DTOField(default=[], description='List of series block outputs')
    _iterator: str = PrivateAttr('block_data')


def validate_as_of(as_of):
    return isinstance(as_of, datetime) and as_of.tzinfo is not None
