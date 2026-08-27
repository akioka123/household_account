# コーディング指示（索引）
このプロジェクトは t-wada 流DDDを前提に、ドメイン中心で組み立てる。TDD（Red→Green→Refactor）を必須とし、依存方向はオニオン（内側へ）を厳守する。実装時は「画面/DBから作らない」こと。まずユースケース→ドメイン→永続化→UI配線の順で進める。

参照：
- アーキテクチャ @01_architecture.md
- 依存禁止/境界 @02_dependency_rules.md
- 命名/スタイル @03_style.md
- TDD運用 @04_tdd.md
- ディレクトリ @05_layout.md
- Port/DI @06_ports_di.md
