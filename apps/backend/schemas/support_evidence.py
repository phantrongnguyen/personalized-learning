from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SnapshotReviewIn(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    snapshot_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    review_scope: Literal['aggregate_only', 'source_verified', 'demonstration']
    source_reference: str = Field(min_length=5, max_length=500)
    review_note: str = Field(min_length=20, max_length=2000)
    activity_complete: bool = Field(strict=True)
    assessments_complete: bool = Field(strict=True)
    acknowledged_limitations: Literal[True]

    @model_validator(mode='after')
    def validate_scope(self):
        complete = self.activity_complete or self.assessments_complete
        if self.review_scope == 'aggregate_only' and complete:
            raise ValueError('Kiểm tra số liệu tổng hợp không chứng minh độ đầy đủ nguồn')
        if self.review_scope == 'source_verified' and not complete:
            raise ValueError('Cần xác nhận ít nhất một phạm vi đã đối chiếu nguồn')
        return self
