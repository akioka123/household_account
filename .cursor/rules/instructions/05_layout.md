# 指示：ディレクトリ/モジュール配置
基本構造は以下。domainにモデルと規則、applicationにユースケースとPort、infrastructureにDB等の実装、presentationにFastAPI/テンプレを置く。testsはレイヤ別に分割する。

例：
app/domain/model, app/domain/service
app/application/usecase, app/application/port
app/infrastructure/persistence
app/presentation/web
tests/unit/domain, tests/unit/application, tests/integration

参照：
- Port/DI @06_ports_di.md
- サンプル構成 @sample/README.md
