from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import Session

from db.tables.base import Base


class ThyssenInvoices(Base):
    """Table for storing Thyssen document processing records."""

    __tablename__ = "thyssen_invoices"

    id = Column(Integer, primary_key=True, index=True)
    document_connector_id = Column(String(500), nullable=True, index=True)  # B/L number for linking
    document_type = Column(String(100), nullable=False)  # "master_bill" or "invoice"
    document_uuid = Column(String(500), nullable=False, index=True)  # B/L number or reference number
    document_uuid_type = Column(String(100), nullable=False)  # "bl_number" or "reference_number"
    document_data = Column(JSON, nullable=True)  # Extracted document data
    document_metadata = Column(JSON, nullable=True)  # File metadata (filename, content_type, file_size, etc.)
    processing_status = Column(String(50), nullable=False, default="pending")  # Core operational field
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)  # Record creation timestamp
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # Record update timestamp


def list_thyssen_invoices(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    document_type: Optional[str] = None,
    document_connector_id: Optional[str] = None,
) -> List[ThyssenInvoices]:
    """List Thyssen documents with optional filtering."""
    query = db.query(ThyssenInvoices)

    if document_type:
        query = query.filter(ThyssenInvoices.document_type == document_type)

    if document_connector_id:
        query = query.filter(ThyssenInvoices.document_connector_id == document_connector_id)

    return query.order_by(ThyssenInvoices.id.desc()).offset(offset).limit(limit).all()


def get_thyssen_invoice(db: Session, document_id: int) -> Optional[ThyssenInvoices]:
    """Get a specific Thyssen document by ID."""
    return db.query(ThyssenInvoices).filter(ThyssenInvoices.id == document_id).first()


def get_thyssen_invoice_by_uuid(
    db: Session, document_uuid: str, document_type: Optional[str] = None
) -> Optional[ThyssenInvoices]:
    """Get a Thyssen document by UUID and optionally type."""
    query = db.query(ThyssenInvoices).filter(ThyssenInvoices.document_uuid == document_uuid)
    if document_type:
        query = query.filter(ThyssenInvoices.document_type == document_type)
    return query.first()


def find_bl_number_by_reference(db: Session, reference: str) -> Optional[str]:
    """Find B/L number by looking up a reference number in invoices."""
    # First try to find an invoice with this reference
    invoice_doc = (
        db.query(ThyssenInvoices)
        .filter(ThyssenInvoices.document_uuid == reference, ThyssenInvoices.document_type == "invoice")
        .first()
    )

    if invoice_doc and invoice_doc.document_connector_id:
        return invoice_doc.document_connector_id

    # If not found, try to find a master bill with this UUID
    master_bill = (
        db.query(ThyssenInvoices)
        .filter(ThyssenInvoices.document_uuid == reference, ThyssenInvoices.document_type == "master_bill")
        .first()
    )

    if master_bill:
        return master_bill.document_uuid

    return None


def create_thyssen_invoice(
    db: Session,
    document_type: str,
    document_uuid: str,
    document_uuid_type: str,
    document_connector_id: Optional[str] = None,
    document_data: Optional[dict] = None,
    document_metadata: Optional[dict] = None,
    processing_status: str = "pending",
) -> ThyssenInvoices:
    """Create a new Thyssen document record."""
    document = ThyssenInvoices(
        document_type=document_type,
        document_uuid=document_uuid,
        document_uuid_type=document_uuid_type,
        document_connector_id=document_connector_id,
        document_data=document_data,
        document_metadata=document_metadata,
        processing_status=processing_status,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def update_thyssen_invoice(
    db: Session,
    document_id: int,
    document_data: Optional[dict] = None,
    document_metadata: Optional[dict] = None,
    processing_status: Optional[str] = None,
) -> Optional[ThyssenInvoices]:
    """Update a Thyssen document record."""
    document = db.query(ThyssenInvoices).filter(ThyssenInvoices.id == document_id).first()
    if document:
        if document_data is not None:
            document.document_data = document_data

        if processing_status is not None:
            document.processing_status = processing_status

        if document_metadata is not None:
            # Update existing metadata or create new
            existing_metadata = document.document_metadata or {}
            existing_metadata.update(document_metadata)
            document.document_metadata = existing_metadata

        db.commit()
        db.refresh(document)
    return document


# Helper functions for accessing metadata fields
def get_original_filename(document: ThyssenInvoices) -> Optional[str]:
    """Get original filename from metadata."""
    if document.document_metadata:
        return document.document_metadata.get("original_filename")
    return None


def set_processing_status(db: Session, document_id: int, status: str) -> Optional[ThyssenInvoices]:
    """Convenience function to update just the processing status."""
    return update_thyssen_invoice(db, document_id, document_metadata={"processing_status": status})
