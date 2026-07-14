# ── 视频上传 ──────────────────────────────────────────────────


class VideoUploadResponse(BaseModel):
    url: str
    original_name: str
    size: int
    transcoded: bool


@router.post("/upload-video", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传视频文件（mp4/webm），返回可访问的媒体 URL"""
    result = await MediaService.handle_video_upload(
        file=file,
        user_id=current_user.id,
        transcode=True,
    )
    return VideoUploadResponse(**result)


@router.post("/batch-import")
async def batch_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导入名片(CSV)"""
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("gbk", errors="replace")
    result = await BrochureService.batch_import_from_csv(db, current_user.id, csv_text)
    return {"code": 200, "data": result}

@router.post("/batch-export")
async def batch_export(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导出名片为CSV"""
    csv_output = await BrochureService.batch_export_csv(db, current_user.id, {"status": status} if status else None)
    from fastapi.responses import StreamingResponse
    import io
    return StreamingResponse(
        io.BytesIO(csv_output.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=business_cards.csv"},
    )
