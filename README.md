# Noyo Segments API

A FastAPI backend for managing people and assigning them to date-based segments.

## Tech Stack
- Python 3.11+
- FastAPI, Uvicorn
- SQLAlchemy (SQLite)
- Pydantic
- Pytest

## Setup & Running
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install fastapi uvicorn sqlalchemy pydantic pytest httpx email-validator`
4. `uvicorn main:app --reload`
5. Run tests: `pytest -v`

## Business Rules
- **Email Uniqueness:** Every person must have a unique email address.
- **Date Validation:** A segment's `end_date` must be greater than or equal to its `start_date`.
- **Segment Uniqueness:** Segment names must be unique.
- **Overlap Prevention:** A person cannot be assigned to a new segment if it overlaps in date range with an existing segment they belong to.
- **Safe Deletion:** Deleting a person automatically removes their segment assignments to prevent orphaned records.
- **Pagination:** The `/people/` endpoint supports `page` and `limit` query parameters.
