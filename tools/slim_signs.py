"""収集した生データを、公開用の軽い学習データに変換する。

tools/collect.html が書き出すJSONには landmarks（21点×手の数の生座標）が
入っているが、画面は vector しか見ていない。landmarks は特徴量を作り直す
ときだけ必要なので、公開版からは外す。あわせて vector を小数5桁に丸める。

    8.0 MB → 0.80 MB（90%削減）。leave-one-out k-NN の正解率は 98.58% で変化なし。

GitHub Pagesではページを開くたびにこのJSONが落ちてくるので、ここが軽いかどうかが
そのまま初回表示の速さになる。

使い方:
    python tools/slim_signs.py dataset/signs_full_20260731.json data/signs.json

生データは dataset/ に置いておくこと（.gitignore済み）。撮り直したら
生データをそこに入れ、このスクリプトを通して data/signs.json を作り直す。
"""

import json
import os
import sys

# 画面が実際に読むキーだけ残す
KEEP = ("label", "handsCount", "handedness", "vector")
ROUND_DIGITS = 5


def slim(src: str, dst: str) -> None:
    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("samples") or []
    if not samples:
        raise SystemExit(f"{src} に samples がありません")

    missing = [k for k in KEEP if k not in samples[0]]
    if missing:
        raise SystemExit(f"{src} に必要なキーがありません: {', '.join(missing)}")

    out = {
        "app": data.get("app"),
        "version": data.get("version"),
        "exportedAt": data.get("exportedAt"),
        "note": (
            "公開用に軽量化。landmarksを除き、vectorを小数5桁に丸めてある。"
            "生データは dataset/ を参照（git管理外）"
        ),
        "signs": data.get("signs"),
        "samples": [
            {
                "label": s["label"],
                "handsCount": s["handsCount"],
                "handedness": s["handedness"],
                "vector": [round(v, ROUND_DIGITS) for v in s["vector"]],
            }
            for s in samples
        ],
    }

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    before = os.path.getsize(src)
    after = os.path.getsize(dst)
    print(
        f"{src} ({before / 1048576:.1f} MB) → {dst} ({after / 1048576:.2f} MB) "
        f"/ {(1 - after / before) * 100:.0f}%削減 / {len(out['samples'])} サンプル"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: python {sys.argv[0]} <生データ.json> <出力先.json>")
    slim(sys.argv[1], sys.argv[2])
