# pylint: disable=no-name-in-module
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from typing_extensions import Self, override
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Angle as ProtoAngle
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Block as ProtoBlock
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Entity as ProtoEntity
from yandex.cloud.ai.ocr.v1.ocr_pb2 import LayoutType as ProtoLayoutType
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Line as ProtoLine
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Picture as ProtoPicture
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Polygon as ProtoPolygon
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Table as ProtoTable
from yandex.cloud.ai.ocr.v1.ocr_pb2 import TableCell as ProtoTableCell
from yandex.cloud.ai.ocr.v1.ocr_pb2 import TextAnnotation as ProtoTextAnnotation
from yandex.cloud.ai.ocr.v1.ocr_pb2 import Word as ProtoWord

from yandex_ai_studio_sdk._types.proto import Context, ProtoBased, ProtoBasedWithCtx, SDKType
from yandex_ai_studio_sdk._types.result import BaseResult
from yandex_ai_studio_sdk._types.sequence import TupleSequence

__all__ = [
    'PageContext',
    'TextAnnotation',
    'EntitiesContext',
    'Vertex', 'Entity', 'Word', 'Line', 'Block',
    'TableCell', 'Table', 'Picture',
]


# Maps non-zero proto Angle enum values to degrees.
# ANGLE_UNSPECIFIED and ANGLE_0 both map to 0, handled by the .get() default.
_ANGLE_TO_DEGREES: dict[int, int] = {
    ProtoAngle.ANGLE_90: 90,
    ProtoAngle.ANGLE_180: 180,
    ProtoAngle.ANGLE_270: 270,
}


def _vertices_from_proto(proto: ProtoPolygon, sdk: SDKType) -> tuple[Vertex, ...]:
    return tuple(Vertex(x=v.x, y=v.y) for v in proto.vertices)


@dataclass(frozen=True, kw_only=True)
class EntitiesContext(Context):
    """Context carrying recognized entities for entity-index resolution."""
    entities: tuple[Entity, ...]


@dataclass(frozen=True, kw_only=True)
class PageContext(Context):
    """Context carrying the page number for a single-page recognition response."""
    page: int


# Maps proto LayoutType int values to their short lowercase names.
_LAYOUT_TYPE_INT_TO_NAME: dict[int, str] = {
    v: k.removeprefix('LAYOUT_TYPE_').lower()
    for k, v in ProtoLayoutType.items()
}


class Vertex(NamedTuple):
    """A point on the image in pixels."""
    x: int
    y: int


@dataclass(frozen=True, kw_only=True)
class Entity(ProtoBased[ProtoEntity]):
    """A named entity recognized in the text."""
    #: Entity type name (e.g. ``"name"``, ``"date"``).
    name: str
    #: Recognized entity text.
    text: str

    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: ProtoEntity, sdk: SDKType) -> Self:
        return cls(name=proto.name, text=proto.text)


@dataclass(frozen=True, kw_only=True)
class Word(ProtoBasedWithCtx[ProtoWord, EntitiesContext]):
    """A single recognized word."""
    #: Bounding polygon of the word as an ordered tuple of vertices.
    bounding_box: tuple[Vertex, ...]
    #: Recognized word text.
    text: str
    #: Named entity this word belongs to, or ``None``.
    entity: Entity | None

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoWord, sdk: SDKType, ctx: EntitiesContext) -> Self:
        entity: Entity | None = None
        # entity_index == -1 means no entity; non-negative index is a valid reference
        if proto.entity_index != -1 and 0 <= proto.entity_index < len(ctx.entities):
            entity = ctx.entities[proto.entity_index]
        return cls(
            bounding_box=_vertices_from_proto(proto.bounding_box, sdk),
            text=proto.text,
            entity=entity,
        )


@dataclass(frozen=True, kw_only=True)
class Line(TupleSequence[Word], ProtoBasedWithCtx[ProtoLine, EntitiesContext]):
    """A line of recognized text. Iterates over its words."""
    #: Bounding polygon of the line as an ordered tuple of vertices.
    bounding_box: tuple[Vertex, ...]
    #: Recognized text of the line.
    text: str
    #: Words in this line.
    words: tuple[Word, ...]
    #: Rotation angle of the line in degrees (0, 90, 180, 270).
    orientation: int

    @property
    @override
    def _items(self) -> tuple[Word, ...]:
        return self.words

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoLine, sdk: SDKType, ctx: EntitiesContext) -> Self:
        return cls(
            bounding_box=_vertices_from_proto(proto.bounding_box, sdk),
            text=proto.text,
            words=tuple(
                Word._from_proto(proto=w, sdk=sdk, ctx=ctx)
                for w in proto.words
            ),
            orientation=_ANGLE_TO_DEGREES.get(proto.orientation, 0),
        )


@dataclass(frozen=True, kw_only=True)
class Block(TupleSequence[Line], ProtoBasedWithCtx[ProtoBlock, EntitiesContext]):
    """A block of recognized text. Iterates over its lines."""
    #: Bounding polygon of the block as an ordered tuple of vertices.
    bounding_box: tuple[Vertex, ...]
    #: Lines in this block.
    lines: tuple[Line, ...]
    #: Languages detected in this block.
    languages: tuple[str, ...]
    #: Layout type of this block as a lowercase string (e.g. ``'text'``, ``'header'``).
    layout_type: str

    @property
    def text(self) -> str:
        """Full text of the block as a concatenation of its lines."""
        return '\n'.join(line.text for line in self.lines)

    @property
    @override
    def _items(self) -> tuple[Line, ...]:
        return self.lines

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoBlock, sdk: SDKType, ctx: EntitiesContext) -> Self:
        return cls(
            bounding_box=_vertices_from_proto(proto.bounding_box, sdk),
            lines=tuple(
                Line._from_proto(proto=line, sdk=sdk, ctx=ctx)
                for line in proto.lines
            ),
            languages=tuple(lang.language_code for lang in proto.languages),
            layout_type=_LAYOUT_TYPE_INT_TO_NAME.get(proto.layout_type, '<unknown>'),
        )


@dataclass(frozen=True, kw_only=True)
class TableCell(ProtoBased[ProtoTableCell]):
    """A cell in a recognized table."""
    #: Bounding polygon of the cell as an ordered tuple of vertices.
    bounding_box: tuple[Vertex, ...]
    #: Row index (0-based).
    row_index: int
    #: Column index (0-based).
    column_index: int
    #: Number of columns this cell spans.
    column_span: int
    #: Number of rows this cell spans.
    row_span: int
    #: Text content of the cell.
    text: str

    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: ProtoTableCell, sdk: SDKType) -> Self:
        return cls(
            bounding_box=_vertices_from_proto(proto.bounding_box, sdk),
            row_index=proto.row_index,
            column_index=proto.column_index,
            column_span=proto.column_span,
            row_span=proto.row_span,
            text=proto.text,
        )


@dataclass(frozen=True, kw_only=True)
class Table(TupleSequence[TableCell], ProtoBased[ProtoTable]):
    """A recognized table. Iterates over its cells."""
    #: Bounding polygon of the table as an ordered tuple of vertices.
    bounding_box: tuple[Vertex, ...]
    #: Number of rows.
    row_count: int
    #: Number of columns.
    column_count: int
    #: Table cells.
    cells: tuple[TableCell, ...]

    @property
    @override
    def _items(self) -> tuple[TableCell, ...]:
        return self.cells

    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: ProtoTable, sdk: SDKType) -> Self:
        return cls(
            bounding_box=_vertices_from_proto(proto.bounding_box, sdk),
            row_count=proto.row_count,
            column_count=proto.column_count,
            cells=tuple(TableCell._from_proto(proto=c, sdk=sdk) for c in proto.cells),
        )


@dataclass(frozen=True, kw_only=True)
class Picture(ProtoBased[ProtoPicture]):
    """A picture location detected in the document."""
    #: Bounding polygon of the picture as an ordered tuple of vertices.
    bounding_box: tuple[Vertex, ...]
    #: Confidence score of the detection.
    score: float

    @classmethod
    @override
    # pylint: disable-next=unused-argument
    def _from_proto(cls, *, proto: ProtoPicture, sdk: SDKType) -> Self:
        return cls(
            bounding_box=_vertices_from_proto(proto.bounding_box, sdk),
            score=proto.score,
        )


@dataclass(frozen=True, kw_only=True)
class TextAnnotation(BaseResult, ProtoBasedWithCtx[ProtoTextAnnotation, PageContext]):
    """Full text recognition result for a single page."""
    #: Page number (0-indexed) in a multi-page document (e.g. PDF). Always 0 for images.
    page: int
    #: Page width in pixels.
    width: int
    #: Page height in pixels.
    height: int
    #: Page rotation angle in degrees (0, 90, 180, 270).
    rotate: int
    #: Full recognized text of the page.
    full_text: str
    #: Full text in Markdown format (available for ``markdown`` and ``math-markdown`` models).
    markdown: str
    #: Recognized text blocks.
    blocks: tuple[Block, ...]
    #: Recognized named entities.
    entities: tuple[Entity, ...]
    #: Recognized tables.
    tables: tuple[Table, ...]
    #: Detected pictures.
    pictures: tuple[Picture, ...]

    @classmethod
    @override
    def _from_proto(cls, *, proto: ProtoTextAnnotation, sdk: SDKType, ctx: PageContext) -> Self:
        entities = tuple(Entity._from_proto(proto=e, sdk=sdk) for e in proto.entities)
        entities_ctx = EntitiesContext(entities=entities)
        return cls(
            page=ctx.page,
            width=proto.width,
            height=proto.height,
            rotate=_ANGLE_TO_DEGREES.get(proto.rotate, 0),
            full_text=proto.full_text,
            markdown=proto.markdown,
            blocks=tuple(
                Block._from_proto(proto=b, sdk=sdk, ctx=entities_ctx)
                for b in proto.blocks
            ),
            entities=entities,
            tables=tuple(Table._from_proto(proto=t, sdk=sdk) for t in proto.tables),
            pictures=tuple(Picture._from_proto(proto=p, sdk=sdk) for p in proto.pictures),
        )
