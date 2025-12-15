# 指示：Port/Adapter と DI
外部依存は必ずPort（Protocol）にする（application/port）。UseCaseはPortをコンストラクタDIで受け取り、具象をnewしない。FastAPIのdependencyでPort実装（infrastructure Adapter）を注入する。Portは小さく、ユースケースが必要な操作だけを定義する。domainはPortを知らない（必要ならapplicationが橋渡し）。

参照：
- サンプル：Port @sample/app/application/port/income_repository.py
- サンプル：DI配線 @sample/app/presentation/web/router.py
