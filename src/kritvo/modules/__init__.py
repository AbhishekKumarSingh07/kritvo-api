"""Feature modules (identity, jobs, inventory, ...), one package each. See LLD section 1.2.

Each module has: api.py (FastAPI router), service.py (public interface and transactions),
models.py (SQLAlchemy), schemas.py (Pydantic), events.py and tasks.py.
Create new modules with the /new-module skill in Claude Code.
"""
