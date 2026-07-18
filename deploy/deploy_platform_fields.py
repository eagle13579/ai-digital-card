#!/usr/bin/env python3
"""Deploy Platform model changes to production"""
import sys

MODEL_PATH = "/var/www/ai-digital-card/backend/app/models/platform.py"
ROUTER_PATH = "/var/www/ai-digital-card/backend/app/routers/platform_router.py"

# === Update model ===
with open(MODEL_PATH) as f:
    model = f.read()

if "province" not in model:
    model = model.replace(
        "    description: Mapped[str] = mapped_column(Text, default=\"\", comment=\"平台描述\")",
        """    description: Mapped[str] = mapped_column(Text, default="", comment="平台描述")
    province: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="省份")
    city: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="城市")
    district: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="区/县")
    contact_name: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="联系人")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="联系电话")
    industries: Mapped[str | None] = mapped_column(Text, nullable=True, comment="行业标签(JSON数组)")"""
    )
    with open(MODEL_PATH, 'w') as f:
        f.write(model)
    print("Model updated")
else:
    print("Model already has province field")

# === Update router schema ===
with open(ROUTER_PATH) as f:
    router = f.read()

if "province: Optional[str]" not in router:
    router = router.replace(
        '    description: str = Field("", max_length=2048, description="平台描述")',
        """    description: str = Field("", max_length=2048, description="平台描述")
    province: Optional[str] = Field(None, max_length=32, description="省份")
    city: Optional[str] = Field(None, max_length=32, description="城市")
    district: Optional[str] = Field(None, max_length=32, description="区/县")
    contact_name: Optional[str] = Field(None, max_length=64, description="联系人")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    industries: Optional[str] = Field(None, max_length=1024, description="行业标签(JSON数组)")"""
    )
    with open(ROUTER_PATH, 'w') as f:
        f.write(router)
    print("Router schema updated")
else:
    print("Router already has province fields")

# === DB migration: add columns ===
import subprocess
result = subprocess.run([
    "psql", "-h", "localhost", "-U", "aicard", "-d", "aicard_db",
    "-c", """
    ALTER TABLE platforms ADD COLUMN IF NOT EXISTS province VARCHAR(32);
    ALTER TABLE platforms ADD COLUMN IF NOT EXISTS city VARCHAR(32);
    ALTER TABLE platforms ADD COLUMN IF NOT EXISTS district VARCHAR(32);
    ALTER TABLE platforms ADD COLUMN IF NOT EXISTS contact_name VARCHAR(64);
    ALTER TABLE platforms ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
    ALTER TABLE platforms ADD COLUMN IF NOT EXISTS industries TEXT;
    SELECT column_name FROM information_schema.columns WHERE table_name='platforms' ORDER BY ordinal_position;
    """
], capture_output=True, text=True, env={"PGPASSWORD": "AICard_PG_2026!", "PATH": "/usr/bin:/bin"})
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
if result.returncode != 0:
    print("Migration error:", result.stderr[-300:])
else:
    print("Migration completed")
