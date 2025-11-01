#!/usr/bin/env python3
"""Multi-Agent Competition System - NiceGUI Interface (Hugging Face Spaces)."""

import sys
from pathlib import Path

# 共通コードへのパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))

# 既存のNiceGUIアプリケーションをインポートして実行
from src.main import main

if __name__ == "__main__":
    main()
