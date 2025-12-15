# 指示：アーキテクチャ（オニオン）
レイヤは presentation→application→domain を「呼ぶ」だけ。infrastructure は外側で Port を実装し、domain/application へ依存してよいが、その逆は禁止。計算規則（現金差分、固定費控除、損益）は domain または domain service に閉じ込め、application(usecase)はトランザクション境界とオーケストレーションのみ担当する。

依存方向：
presentation → application → domain
infrastructure → application/domain（Port実装）

参照：
- 依存禁止の詳細 @02_dependency_rules.md
- 進め方の手順 @04_tdd.md
