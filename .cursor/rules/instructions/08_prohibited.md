# 指示：禁止事項（品質劣化を防ぐ）
- domainでSQLAlchemy/Pydantic/FastAPI等をimportしない
- Router内でDB操作や集計計算をしない（UseCaseへ）
- UseCaseに計算ロジックを詰めない（domainへ寄せる）
- utils.py巨大化を許可しない（責務で分割）
- テストなしで進めない（最小でもdomain→application）
- infrastructure具象をapplicationから参照しない（Port越し）

参照：
- 依存禁止 @02_dependency_rules.md
- 進め方 @07_steps.md
