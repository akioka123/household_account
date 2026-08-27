# 指示：命名・コーディング規約
Python 3.12+、型ヒント必須。Value Object は原則 immutable（dataclass(frozen=True)）。Entity/VO/UseCase/Repository の命名をDDDに寄せる：Entity/VOは名詞、UseCaseは動詞+目的語、PortはXxxRepository、実装はSqlAlchemyXxxRepository等。None許容は境界層（presentation/application）に閉じ込め、domain は不変条件を例外で守る。

参照：
- ディレクトリ @05_layout.md
- テスト方針 @04_tdd.md
