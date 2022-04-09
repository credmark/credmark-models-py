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
)


from credmark.dto import (
    GenericDTO,
    DTOField,
    IterableListGenericDTO,
    PrivateAttr,
)

# pylint:disable=locally-disabled,too-many-instance-attributes

ChefT = TypeVar('ChefT')  # Chef return type
PlanT = TypeVar('PlanT')  # Plan return type


class Recipe(GenericDTO, Generic[ChefT, PlanT]):
    cache_keywords: List[Any]  # Unique keywords in Plan's Cache
    target_key: str  # Unique key in Market
    method: str
    input: dict
    post_proc: Callable[[Any, ChefT], PlanT]
    error_handle: Callable[[Any, Exception], Tuple[str, PlanT]]
    chef_return_type: Type[ChefT]
    plan_return_type: Type[PlanT]


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
