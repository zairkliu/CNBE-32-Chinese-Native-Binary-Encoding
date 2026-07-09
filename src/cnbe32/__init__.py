"""CNBE-32: Chinese Native Binary Encoding - Python SDK"""

__version__ = "1.0.1"

from .constants import (
    CJK_UNICODE_COUNT,
    CJK_UNICODE_START,
    CNBE_DEFAULT_DATA_DIR,
    CNBE_DEFAULT_ENCODING,
    CNBE_EXT_FLAGS_MAX,
    CNBE_EXT_FLAGS_MIN,
    CNBE_RADIX_MAX,
    CNBE_RADIX_MIN,
    CNBE_STROKE_MAX,
    CNBE_STROKE_MIN,
    CNBE_STRUCT_MAX,
    CNBE_STRUCT_MIN,
    CNBE_SUB_TYPE_MAX,
    CNBE_SUB_TYPE_MIN,
    CNBE_VALUE_MAX,
    CNBE_VALUE_MIN,
    EXT_MASK,
    EXT_SHIFT,
    INDEX_MASK,
    INDEX_SHIFT,
    RADIX_MASK,
    RADIX_SHIFT,
    RADIX_TABLE_FILE,
    SKILL_TABLE_FILE,
    STROKE_MASK,
    STROKE_SHIFT,
    STRUCT_MASK,
    STRUCT_NAMES,
    STRUCT_SHIFT,
)
from .core import (
    CNBE32,
    bit_hamming_distance,
    decode_cnbe,
    encode_cnbe,
    field_weighted_distance,
    hamming_distance,  # deprecated — use field_weighted_distance or bit_hamming_distance
)
from .db import (
    batch,
    by_radix,
    close,
    count,
    lookup,
    resolve_db_path,
    search,
    stats,
)
from .encoders import (
    BlackHoleEncoder,
    MathEncoder,
    OneHotEncoder,
    RandomEncoder,
    RawEncoder,
    SocialEncoder,
    TreeEncoder,
    TyphoonEncoder,
)
from .exceptions import (
    CNBECharNotInTableError,
    CNBEError,
    CNBEFormatError,
    CNBEStructureError,
    CNBEValueError,
)
from .skill_table import SkillTable
