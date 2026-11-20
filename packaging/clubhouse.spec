# PyInstaller spec for Clubhouse: a one-folder Windows build (dist\Clubhouse\Clubhouse.exe).
# Build:  .venv\Scripts\python.exe -m PyInstaller packaging\clubhouse.spec --noconfirm --distpath dist --workpath build
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "app" / "clubhouse.py")],
    pathex=[str(ROOT / "decoder"), str(ROOT / "app")],
    datas=[(str(ROOT / "app" / "ui"), "ui")],
    hiddenimports=["updater", "version", "mlb26save.extract", "mlb26save.snapshots", "mlb26save.history", "mlb26save.franchises",
                   "mlb26save.container", "mlb26save.database"],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "PIL", "pytest", "mlb26save.edit"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Clubhouse",
    icon=str(ROOT / "packaging" / "clubhouse.ico"),
    version=str(ROOT / "packaging" / "version_info.txt"),
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Clubhouse")
