"""Import a bounded OULAD cohort into a separately named demo database."""
import argparse
import asyncio
import hashlib
import random
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from load_oulad_case import StudentProfile, load, verify
from prepare_oulad_case import FILES, build_case


def source_checksums(directory):
    checksums = {}
    for name in FILES:
        path = directory / f"{name}.parquet"
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        checksums[name] = digest.hexdigest()
    return checksums


def eligible_ids(directory, module, presentation, limit, seed, selection):
    filters = [("code_module", "=", module), ("code_presentation", "=", presentation)]
    info = pd.read_parquet(directory / "studentInfo.parquet", filters=filters)
    registration = pd.read_parquet(directory / "studentRegistration.parquet", filters=filters)
    course = pd.read_parquet(directory / "courses.parquet", filters=filters)
    if len(course) != 1 or course.iloc[0].module_presentation_length <= 0:
        raise ValueError("Expected one valid presentation")
    cutoff = int(course.iloc[0].module_presentation_length * .75)
    active = registration[
        registration.date_registration.le(cutoff)
        & (registration.date_unregistration.isna() | registration.date_unregistration.gt(cutoff))
    ]
    ids = sorted(set(info.id_student.astype(int)) & set(active.id_student.astype(int)))
    if selection == "random":
        ids = sorted(random.Random(seed).sample(ids, min(limit, len(ids))))
    return ids[:limit]


async def existing_ids(url):
    engine = create_async_engine(url)
    try:
        async with async_sessionmaker(engine)() as db:
            codes = (await db.execute(select(StudentProfile.student_code).where(
                StudentProfile.student_code.like("OULAD-%")))).scalars().all()
            return set(codes)
    finally:
        await engine.dispose()


async def import_cases(cases, url, lecturer_code):
    for case, features in cases:
        await load(case, features, url, lecturer_code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", required=True, type=Path)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--lecturer-code", required=True)
    parser.add_argument("--module", default="AAA")
    parser.add_argument("--presentation", default="2013J")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--selection", choices=("first", "random"), default="random")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    url = make_url(args.database_url)
    if not url.database or not url.database.endswith("_oulad"):
        parser.error("Only a separately named *_oulad database is allowed")
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    directory = args.parquet_dir.resolve()
    hashes = source_checksums(directory)
    candidates = eligible_ids(directory, args.module, args.presentation, args.limit,
                              args.seed, args.selection)
    async_url = url.set(drivername="postgresql+asyncpg").render_as_string(hide_password=False)
    existing = asyncio.run(existing_ids(async_url))
    cases = []
    for student_id in candidates:
        if f"OULAD-{student_id}" in existing:
            continue
        case = build_case(directory, args.module, args.presentation, student_id, hashes)
        cases.append((case, verify(case, directory, hashes)))
    print(f"Verified {len(cases)} new OULAD cases of {len(candidates)} selected; "
          f"{len(candidates) - len(cases)} already imported.")
    if not args.apply:
        print("Dry run: no database write. Pass --apply to import into the isolated database.")
        return
    asyncio.run(import_cases(cases, async_url, args.lecturer_code))


if __name__ == "__main__":
    main()
