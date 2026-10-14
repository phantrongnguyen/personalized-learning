import uuid
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.permissions import RequireRoles
from core.security import get_password_hash
from core.config import settings
from ml.model_loader import load_model
from ml.predictor import predict
from models.user import User, Role
from models.profile import StudentProfile, AdvisorProfile, LecturerProfile
from models.academic import Course, CoursePresentation
from models.assignment import AdvisorStudent, CourseLecturer
from models.ml import MLModel, PredictionRun
from models.feature import StudentFeatureSnapshot
from models.audit import AuditLog
from schemas.auth import UserOut
from schemas.admin import (
    AdminUserCreateIn,
    AdminUserUpdateIn,
    AdminPasswordResetIn,
    AdminPasswordResetOut,
    UserStatusUpdateIn,
    UserRolesUpdateIn,
    CourseCreateIn,
    CoursePresentationCreateIn,
    AssignAdvisorIn,
    AssignLecturerIn,
    MLModelOut,
    ActivateModelIn,
    BatchPredictResultOut,
    AuditLogOut,
)
from services.audit_service import write_audit_log, get_client_ip
from services.prediction_service import generate_database_predictions

router = APIRouter()

# Yêu cầu vai trò ADMIN cho toàn bộ endpoints trong module
require_admin = RequireRoles(["ADMIN"])


async def _load_user_full(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Nạp đầy đủ quan hệ của người dùng để trả về đúng response_model UserOut."""
    query = (
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.student_profile),
            selectinload(User.advisor_profile),
            selectinload(User.lecturer_profile),
        )
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    return result.scalars().first()


# ==============================================================================
# 1. QUẢN TRỊ NGƯỜI DÙNG & PHÂN QUYỀN
# ==============================================================================
@router.get("/users", response_model=List[UserOut], summary="Danh sách người dùng")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.student_profile),
            selectinload(User.advisor_profile),
            selectinload(User.lecturer_profile),
        )
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/users/{user_id}", response_model=UserOut, summary="Xem chi tiết tài khoản")
async def get_user_detail(user_id: uuid.UUID, current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    user = await _load_user_full(db, user_id)
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại")
    return user


@router.put("/users/{user_id}/reset-password", response_model=AdminPasswordResetOut,
            summary="Admin đặt lại mật khẩu tài khoản")
async def reset_user_password(
    user_id: uuid.UUID,
    payload: AdminPasswordResetIn,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin cấp mật khẩu mới, không cần mật khẩu cũ; không trả mật khẩu/hash."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    try:
        user.hashed_password = get_password_hash(payload.new_password.get_secret_value())
        await write_audit_log(
            db, user_id=current_user.id, action="RESET_USER_PASSWORD", target_type="USER",
            target_id=user_id, detail="Quản trị viên đặt lại mật khẩu tài khoản",
            ip_address=get_client_ip(request),
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return {"message": "Đã đặt lại mật khẩu tài khoản", "user_id": user_id}


@router.put("/users/{user_id}", response_model=UserOut, summary="Sửa thông tin tài khoản")
async def edit_user(user_id: uuid.UUID, payload: AdminUserUpdateIn, request: Request,
                    current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    user = await _load_user_full(db, user_id)
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại")
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "Không có thông tin cập nhật")
    profile_fields = {
        "student_code": user.student_profile,
        "lecturer_code": user.lecturer_profile,
        "academic_rank": user.lecturer_profile,
        "office_location": user.advisor_profile,
        "department": user.advisor_profile or user.lecturer_profile,
    }
    for field in fields:
        if field in profile_fields and profile_fields[field] is None:
            raise HTTPException(400, f"Tài khoản không có hồ sơ phù hợp để sửa {field}")
    try:
        for field, value in fields.items():
            setattr(profile_fields[field] if field in profile_fields else user, field, value)
        await write_audit_log(db, user_id=current_user.id, action="UPDATE_USER", target_type="USER",
                              target_id=user.id, detail=f"Cập nhật các trường: {', '.join(fields)}", ip_address=get_client_ip(request))
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Email, mã sinh viên hoặc mã giảng viên đã được sử dụng")
    return await _load_user_full(db, user_id)


@router.delete("/users/{user_id}", summary="Xóa tài khoản và hồ sơ liên quan")
async def delete_user(user_id: uuid.UUID, request: Request, current_user: User = Depends(require_admin),
                      db: AsyncSession = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(400, "Không thể xóa tài khoản đang sử dụng")
    user = await _load_user_full(db, user_id)
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại")
    try:
        await write_audit_log(db, user_id=current_user.id, action="DELETE_USER", target_type="USER",
                              target_id=user.id, detail=f"Xóa tài khoản {user.email}", ip_address=get_client_ip(request))
        # Database foreign keys cascade profiles and dependent academic data.
        await db.execute(delete(User).where(User.id == user_id).execution_options(synchronize_session=False))
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Không thể xóa do tài khoản còn dữ liệu liên kết. Hãy khóa tài khoản.")
    return {"message": "Đã xóa tài khoản và dữ liệu liên quan"}


@router.post("/users", response_model=UserOut, summary="Tạo mới tài khoản người dùng")
async def create_new_user(
    payload: AdminUserCreateIn,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Kiểm tra trùng email
    check = await db.execute(select(User).where(User.email == payload.email))
    if check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng trong hệ thống",
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        is_active=True,
    )

    # Gán vai trò
    roles_query = select(Role).where(Role.code.in_(payload.role_codes))
    roles_res = await db.execute(roles_query)
    user.roles = list(roles_res.scalars().all())

    db.add(user)
    await db.flush()

    # Tự động tạo profile tương ứng nếu có thông tin
    if "STUDENT" in payload.role_codes and payload.student_code:
        stu_profile = StudentProfile(
            user_id=user.id,
            student_code=payload.student_code,
            gender=payload.gender or "M",
            highest_education=payload.highest_education or "HE Qualification",
            age_band=payload.age_band or "0-35",
        )
        db.add(stu_profile)
    elif "ADVISOR" in payload.role_codes:
        adv_profile = AdvisorProfile(
            user_id=user.id,
            department=payload.department or "Khoa CNTT",
        )
        db.add(adv_profile)
    elif "LECTURER" in payload.role_codes and payload.lecturer_code:
        lec_profile = LecturerProfile(
            user_id=user.id,
            lecturer_code=payload.lecturer_code,
            department=payload.department or "Khoa CNTT",
        )
        db.add(lec_profile)

    await db.commit()
    await db.refresh(user)

    # Ghi vết thao tác tạo tài khoản
    user = await _load_user_full(db, user.id)
    await write_audit_log(
        db,
        user_id=current_user.id,
        action="CREATE_USER",
        target_type="USER",
        target_id=user.id,
        detail=f"Tạo tài khoản {user.email} với vai trò {payload.role_codes}",
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return user


@router.put("/users/{user_id}/status", summary="Kích hoạt hoặc khóa tài khoản")
async def toggle_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateIn,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id and not payload.is_active:
        raise HTTPException(400, "Không thể khóa tài khoản đang sử dụng")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

    user.is_active = payload.is_active
    db.add(user)
    await write_audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE_USER_STATUS",
        target_type="USER",
        target_id=user.id,
        detail=f"{'Kích hoạt' if payload.is_active else 'Khóa'} tài khoản {user.email}",
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"message": f"Tài khoản đã được {'kích hoạt' if payload.is_active else 'khóa'}"}


@router.post("/users/{user_id}/roles", response_model=UserOut, summary="Cập nhật vai trò của người dùng")
async def update_user_roles(
    user_id: uuid.UUID,
    payload: UserRolesUpdateIn,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người dùng không tồn tại")

    if not payload.role_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách vai trò không được để trống",
        )

    roles_res = await db.execute(select(Role).where(Role.code.in_(payload.role_codes)))
    roles = list(roles_res.scalars().all())
    if len(roles) != len(set(payload.role_codes)):
        found = {r.code for r in roles}
        missing = [c for c in payload.role_codes if c not in found]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vai trò không hợp lệ: {missing}",
        )

    user.roles = roles
    db.add(user)
    await write_audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE_USER_ROLES",
        target_type="USER",
        target_id=user.id,
        detail=f"Gán vai trò {payload.role_codes} cho {user.email}",
        ip_address=get_client_ip(request),
    )
    await db.commit()

    return await _load_user_full(db, user_id)


# ==============================================================================
# 2. QUẢN LÝ ĐÀO TẠO & PHÂN CÔNG
# ==============================================================================
@router.get("/academic/courses", summary="Danh sách học phần OULAD")
async def list_courses(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Course).order_by(Course.code_module)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/academic/courses", summary="Tạo mới học phần")
async def create_course(
    payload: CourseCreateIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    check = await db.execute(select(Course).where(Course.code_module == payload.code_module))
    if check.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã môn học đã tồn tại")

    course = Course(
        code_module=payload.code_module,
        name=payload.name,
        credits_default=payload.credits_default,
        description=payload.description,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.post("/academic/presentations", summary="Mở kỳ học / lớp học phần")
async def create_presentation(
    payload: CoursePresentationCreateIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    pres = CoursePresentation(
        course_id=payload.course_id,
        code_presentation=payload.code_presentation,
        module_presentation_length=payload.module_presentation_length,
        start_date=payload.start_date,
    )
    db.add(pres)
    await db.commit()
    await db.refresh(pres)
    return pres


@router.post("/academic/assign-advisor", summary="Phân công GVCN cho sinh viên theo lớp sinh hoạt")
async def assign_advisor_student(
    payload: AssignAdvisorIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rel = AdvisorStudent(
        advisor_id=payload.advisor_id,
        student_id=payload.student_id,
        academic_year=payload.academic_year,
        class_name=payload.class_name,
    )
    db.add(rel)
    await db.commit()
    return {"message": "Phân công GVCN cho sinh viên thành công"}


@router.post("/academic/assign-lecturer", summary="Phân công GVBM phụ trách lớp học phần")
async def assign_lecturer_course(
    payload: AssignLecturerIn,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rel = CourseLecturer(
        lecturer_id=payload.lecturer_id,
        presentation_id=payload.presentation_id,
        role_in_course=payload.role_in_course,
    )
    db.add(rel)
    await db.commit()
    return {"message": "Phân công GVBM phụ trách học phần thành công"}


# ==============================================================================
# 3. QUẢN TRỊ MLOPS & BATCH PREDICTION
# ==============================================================================
@router.get("/ml/models", response_model=List[MLModelOut], summary="Danh sách các phiên bản mô hình ML")
async def list_models(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(MLModel).order_by(MLModel.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/ml/reload", summary="Nạp lại mô hình LightGBM vào bộ nhớ RAM máy chủ")
async def reload_ml_model(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_model = load_model(settings.model_path)
        request.app.state.model = new_model
        await write_audit_log(
            db,
            user_id=current_user.id,
            action="RELOAD_ML_MODEL",
            target_type="ML_MODEL",
            detail=f"Nạp lại mô hình từ {settings.model_path}",
            ip_address=get_client_ip(request),
        )
        await db.commit()
        return {"message": "Nạp lại mô hình vào RAM thành công", "model_info": list(new_model.keys())}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi nạp lại mô hình: {str(e)}"
        )


@router.post("/ml/models/activate", response_model=MLModelOut, summary="Kích hoạt một phiên bản mô hình ML")
async def activate_ml_model(
    payload: ActivateModelIn,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    model = await db.get(MLModel, payload.model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phiên bản mô hình không tồn tại")

    # Chỉ duy nhất một phiên bản được active tại một thời điểm
    await db.execute(update(MLModel).values(is_active=False))
    model.is_active = True
    db.add(model)

    await write_audit_log(
        db,
        user_id=current_user.id,
        action="ACTIVATE_ML_MODEL",
        target_type="ML_MODEL",
        target_id=model.id,
        detail=f"Kích hoạt mô hình {model.model_name} v{model.version}",
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(model)
    return model


@router.post("/ml/batch-predict", response_model=BatchPredictResultOut, summary="Dự báo bằng mô hình active từ snapshot mới nhất")
async def batch_predict_all_students(
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    enrollment_id: Optional[uuid.UUID] = None,
):
    started = time.perf_counter()
    try:
        model, runs = await generate_database_predictions(db, current_user.id, enrollment_id)
        high_risk = sum(run.prediction_label == 1 for run in runs)
        await write_audit_log(
            db, user_id=current_user.id, action="BATCH_PREDICT",
            target_type="ML_MODEL", target_id=model.id,
            detail=f"Dự báo ML thực tế {len(runs)} snapshot; enrollment={enrollment_id or 'ALL'}",
            ip_address=get_client_ip(request),
        )
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except (ValueError, TypeError, KeyError) as exc:
        await db.rollback()
        raise HTTPException(422, "Dữ liệu hoặc đầu vào mô hình không hợp lệ; không lưu dự báo") from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(500, "Không thể chạy/lưu dự báo ML; không lưu kết quả dự phòng") from exc
    return {
        "total_snapshots_scanned": len(runs), "predictions_generated": len(runs),
        "high_risk_count": high_risk, "safe_count": len(runs) - high_risk,
        "execution_time_ms": round((time.perf_counter() - started) * 1000),
    }


# ==============================================================================
# 4. NHẬT KÝ KIỂM TOÁN HỆ THỐNG (AUDIT LOGS)
# ==============================================================================
@router.get("/system/audit-logs", response_model=List[AuditLogOut], summary="Tra cứu nhật ký thao tác hệ thống")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AuditLog, User)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(desc(AuditLog.created_at))
        .offset(skip)
        .limit(limit)
    )
    if action:
        query = query.where(AuditLog.action == action)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_full_name": user.full_name if user else None,
            "user_email": user.email if user else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }
        for log, user in rows
    ]
