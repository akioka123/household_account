# 指示：実装の進め方（固定手順）
1) ユースケースを1つ選ぶ（例：給与登録）
2) 入力/出力を文章で固定（DTO化）
3) 必要なドメイン（VO/Entity/Policy）を洗い出す
4) domainテスト→domain実装（Red/Green）
5) UseCaseテスト（FakeRepo）→UseCase実装
6) infrastructure実装＋integration test
7) presentation配線（htmxは部分更新）
8) リファクタ（依存方向/責務/命名/重複）を必ず実施

参照：
- TDD運用 @04_tdd.md
- 禁止事項 @08_prohibited.md
