import re
from dataclasses import dataclass, field


class POParseError(Exception):
    """Raised when a message can't be parsed into purchase order data."""


HEADER_PATTERN = re.compile(
    r"^(?P<supplier>.+?)\s+(?P<po_id>[A-Za-z0-9][A-Za-z0-9\-_/]*)$"
)
QTY_PATTERN = re.compile(r"^(?P<amount>[\d.,]+)\s*(?P<unit>[a-zA-Z]*)$")
PRICE_PATTERN = re.compile(r"^\$?\s*(?P<amount>[\d.,]+)\s*\$?$")


@dataclass
class POItem:
    description: str
    quantity: float
    unit: str
    unit_price: float

    def to_dict(self) -> dict:
        return {
            "department": "Kitchen",
            "name": self.description,
            "packing": self.unit,
            "price": self.unit_price,
            "qty": self.quantity,
        }


@dataclass
class PurchaseOrder:
    supplier_name: str
    po_id: str
    items: list[POItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "supplier_name": self.supplier_name,
            "po_id": self.po_id,
            "items": [item.to_dict() for item in self.items],
        }


def _parse_item_line(line: str, line_no: int) -> POItem:
    body = line.strip()
    if body.startswith("-"):
        body = body[1:].strip()

    tokens = body.split()
    if len(tokens) < 3:
        raise POParseError(
            f"Line {line_no}: expected '- Description QTY PRICE$', got '{line.strip()}'"
        )

    price_token, qty_token = tokens[-1], tokens[-2]
    description = " ".join(tokens[:-2]).strip()

    qty_match = QTY_PATTERN.match(qty_token)
    if not qty_match:
        raise POParseError(f"Line {line_no}: could not parse quantity '{qty_token}'")

    price_match = PRICE_PATTERN.match(price_token)
    if not price_match:
        raise POParseError(
            f"Line {line_no}: could not parse unit price '{price_token}'"
        )

    if not description:
        raise POParseError(f"Line {line_no}: missing item description")

    try:
        quantity = float(qty_match.group("amount").replace(",", ""))
        unit_price = float(price_match.group("amount").replace(",", ""))
    except ValueError as exc:
        raise POParseError(f"Line {line_no}: invalid number format") from exc

    return POItem(
        description=description,
        quantity=quantity,
        unit=qty_match.group("unit") or "",
        unit_price=unit_price,
    )


def parse_po_message(text: str) -> list[PurchaseOrder]:
    """
    Parses one or more purchase orders from a message like:

        Supplier Name PO-ID
        - Description QTY UnitPrice$
        - Description QTY UnitPrice$

    The PO-ID can be any short code (e.g. "PO-00001", "07", "INV-42") — it
    doesn't have to start with "PO-". Multiple orders can appear
    back-to-back in a single message.
    """
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        raise POParseError("Message is empty.")

    orders: list[PurchaseOrder] = []
    current: PurchaseOrder | None = None

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if line.startswith("-"):
            if current is None:
                raise POParseError(
                    f"Line {line_no}: found an item before any 'Supplier PO-ID' header."
                )
            current.items.append(_parse_item_line(line, line_no))
            continue

        header_match = HEADER_PATTERN.match(line)
        if not header_match:
            raise POParseError(
                f"Line {line_no}: expected 'Supplier Name PO-ID' (e.g. 'Thai Hout PO-00001' "
                f"or 'Sand bakery 07'), got '{line}'"
            )

        current = PurchaseOrder(
            supplier_name=header_match.group("supplier").strip(),
            po_id=header_match.group("po_id").upper(),
        )
        orders.append(current)

    for order in orders:
        if not order.items:
            raise POParseError(f"'{order.po_id}' has no items listed.")

    return orders
