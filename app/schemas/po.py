from pydantic import BaseModel, Field


class POItemIn(BaseModel):
    department: str = "Kitchen"
    name: str
    packing: str = ""
    price: float = Field(ge=0)
    qty: float = Field(gt=0)


class RegeneratePORequest(BaseModel):
    po_id: str = Field(min_length=1)
    supplier_name: str
    items: list[POItemIn] = Field(min_length=1)


class POCallbackRequest(BaseModel):
    """Body GitHub Actions sends back once a PO document is generated."""

    po_db_id: str
    status: str  # "completed" | "failed"
    file_url: str | None = None
    error_message: str | None = None
    github_run_id: str | None = None
