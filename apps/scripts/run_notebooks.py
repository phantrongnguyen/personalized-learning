import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS = ROOT / "apps/notebooks"
NAMES = [
    "11_kiem_tra_bang_chung_goi_y.ipynb",
    "12_goi_y_chien_luoc_co_giai_thich.ipynb",
    "13_danh_gia_ky_thuat_va_phieu_gop_y.ipynb",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", choices=NAMES)
    options = parser.parse_args()
    for name in [options.notebook] if options.notebook else NAMES:
        path = NOTEBOOKS / name
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(notebook, timeout=300, kernel_name="clht-demo",
                                resources={"metadata": {"path": str(NOTEBOOKS)}})
        try:
            client.execute()
        finally:
            nbformat.write(notebook, path)
        print("EXECUTED:", name, flush=True)


if __name__ == "__main__":
    main()
