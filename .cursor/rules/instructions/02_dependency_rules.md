# 指示：依存禁止・境界の固定
domain はフレームワーク/IOに依存しない（FastAPI/SQLAlchemy/Pydantic/Jinja2等のimport禁止）。application は domain に依存してよいが、infrastructure の具象へ依存しない（Port/Protocolのみ）。presentation は UseCase 呼び出しに徹し、DB操作や計算をしない。外部依存（DB/Clock/File）は application/port に Protocol として定義し、infrastructure が実装する。

参照：
- Port/DI @06_ports_di.md
- ディレクトリ例 @05_layout.md
