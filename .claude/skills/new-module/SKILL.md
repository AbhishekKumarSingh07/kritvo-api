---
name: new-module
description: Scaffold a new Kritvo FastAPI feature module (router, service, schemas, models, events, tasks, tests) following LLD section 1.2.
disable-model-invocation: true
argument-hint: "[module_name] [resource-path]"
arguments: [module, resource]
---

Create the FastAPI module `$module` serving `/api/v1/$resource`.

1. Check that `src/kritvo/modules/$module/` does not exist. `$module` must be snake_case; `$resource` must be plural kebab-case (for example `planned-visits`). Read the module's section in `docs/architecture/LLD.md` first.
2. Create these files:

   - `__init__.py`: one-line docstring describing the module.
   - `schemas.py`: Pydantic v2 models. Inputs use `model_config = ConfigDict(extra="forbid")`; outputs use `ConfigDict(from_attributes=True)`.
   - `models.py`: SQLAlchemy 2 typed models (`Mapped[...]`, `mapped_column`), every tenant table with `tenant_id`. Leave empty with a docstring until the database layer exists (TASK-002).
   - `service.py`: the module's public interface. Async functions with full type hints; they own transactions and raise `AppError` for business errors. Other modules may import only this file.
   - `api.py`:

     ```python
     from fastapi import APIRouter

     from kritvo.modules.<module> import service
     from kritvo.modules.<module>.schemas import <Name>Out

     router = APIRouter(prefix="/<resource>", tags=["<module>"])


     @router.get("", response_model=list[<Name>Out])
     async def list_<name_plural>() -> list[<Name>Out]:
         return await service.list_<name_plural>()
     ```

     Add `session`/principal dependencies with `Annotated[..., Depends(...)]` once `kritvo.core.deps` provides them.
   - `events.py` and `tasks.py`: docstrings only until the module emits events or runs background tasks.

3. Include the router in `src/kritvo/main_api.py` inside the `/api/v1` router.
4. Add `tests/modules/$module/test_api.py` with at least one async API test using the `client` fixture, plus unit tests for the service.
5. In `pyproject.toml`, make sure an import-linter contract stops other modules from importing this module's internals (only `service` may be imported across modules). When the second module is added, create it, for example an `independence` contract over `kritvo.modules.*` with `ignore_imports` entries for `service`. Check the installed import-linter version's documentation for the exact syntax, then confirm with `uv run lint-imports` that a deliberate violation fails.
6. Run `uv run kritvo-openapi`, then `uv run ruff check . && uv run ruff format . && uv run mypy src && uv run lint-imports && uv run pytest`.
7. Summarise the files created and the endpoints added.
