# 指示：TDD運用（t-wada流）
必ず Red→Green→Refactor を回す。最初に「仕様をテストに落とす」（失敗確認）→最小実装で通す→重複排除/命名/責務分離を行う。優先順位は domain unit test > application unit test(FakeRepo) > infrastructure integration(SQLite) > UI e2e。ユースケースの入力/出力を文章で固定してからテストを書く。画面やDBから先に作らない。

参照：
- 進め方の具体手順 @07_steps.md
- 禁止事項 @08_prohibited.md
