# 実装サンプル（最小）
目的：ユースケース「給与登録」を TDD + オニオン構造で通す最小例。

参照：
- 指示：@../instructions/00_README.md
- Port/DI：@app/application/port/income_repository.py, @app/presentation/web/router.py
- UseCase：@app/application/usecase/register_income.py
- ドメイン：@app/domain/model/*

実行想定：
- テスト：pytest
- Web：FastAPI（テンプレは最小の骨格のみ）
