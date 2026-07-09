from uuid import uuid4

from .models import OperationStatus

_operations: dict[str, OperationStatus] = {}


def create_operation(operation_type: str, total: int = 0, message: str = "") -> OperationStatus:
    operation = OperationStatus(
        operation_id=str(uuid4()),
        type=operation_type,
        status="running",
        total=total,
        completed=0,
        failed=0,
        message=message,
    )
    _operations[operation.operation_id] = operation
    return operation


def update_operation(
    operation_id: str,
    *,
    status: str | None = None,
    total: int | None = None,
    completed: int | None = None,
    failed: int | None = None,
    message: str | None = None,
    errors: list[str] | None = None,
) -> OperationStatus:
    operation = _operations[operation_id]
    if status is not None:
        operation.status = status
    if total is not None:
        operation.total = total
    if completed is not None:
        operation.completed = completed
    if failed is not None:
        operation.failed = failed
    if message is not None:
        operation.message = message
    if errors is not None:
        operation.errors = errors
    _operations[operation_id] = operation
    return operation


def get_operation(operation_id: str) -> OperationStatus | None:
    return _operations.get(operation_id)
