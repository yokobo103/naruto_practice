"""生のランドマークから特徴量ベクトルを作り直す。

MediaPipeは x を画像の幅、y を高さで正規化して返すため、**カメラの縦横比が変わると
x:y の比が変わる**。normalizeHand は手の大きさで割る等方スケールなので、この歪みを
補正できない。結果、PCで集めたデータをスマホで使うと認識が崩れる
（実測: スマホ縦持ち相当の縦横比で 100% → 75%）。

y を縦横比で割って「幅を単位とする等方座標」に直すと端末に依存しなくなる。
学習データ側も同じ補正をかけた状態で作り直す必要があるため、このスクリプトがある。

    python tools/rebuild_vectors.py dataset/signs_full_20260731.json data/signs.json

index.html の extractFeature / fingerFeatures / normalizeHand の移植。
--verify を付けると、補正なしで計算した結果が元のJSONのvectorと一致するかを確認する
（＝移植が正しいことの証明）。
"""

import json
import math
import os
import sys

# 学習データを撮ったときのカメラの縦横比。
# tools/collect.html は 1280x960 (4:3) を要求している。実機が別の解像度を返していた
# 場合はここを直して作り直すこと。画面の「カメラ」表示で実際の値が確認できる。
TRAIN_ASPECT = 4 / 3

TIPS = [4, 8, 12, 16, 20]
MCPS = [2, 5, 9, 13, 17]
PIPS = [3, 6, 10, 14, 18]
KEY_POINTS = [0, 4, 8, 12, 16, 20]


def to_isotropic(hands, aspect):
    """y を縦横比で割り、幅を単位とする等方座標に直す。"""
    return [[{"x": p["x"], "y": p["y"] / aspect, "z": p.get("z", 0.0)} for p in hand]
            for hand in hands]


def normalize_hand(hand):
    wrist, mid = hand[0], hand[9]
    scale = math.dist(
        (mid["x"], mid["y"], mid.get("z", 0.0)),
        (wrist["x"], wrist["y"], wrist.get("z", 0.0)),
    ) or 1e-6
    return [{
        "x": (p["x"] - wrist["x"]) / scale,
        "y": (p["y"] - wrist["y"]) / scale,
        "z": (p.get("z", 0.0) - wrist.get("z", 0.0)) / scale,
    } for p in hand]


def finger_features(hand):
    out = []
    for tip_i, mcp_i, pip_i in zip(TIPS, MCPS, PIPS):
        tip, mcp, pip = hand[tip_i], hand[mcp_i], hand[pip_i]
        out.append(math.dist((tip["x"], tip["y"], tip["z"]), (mcp["x"], mcp["y"], mcp["z"])))
        out.append(math.dist((tip["x"], tip["y"], tip["z"]), (pip["x"], pip["y"], pip["z"])))
        out.append(mcp["y"] - tip["y"])
    for a in range(len(TIPS)):
        for b in range(a + 1, len(TIPS)):
            p, q = hand[TIPS[a]], hand[TIPS[b]]
            out.append(math.dist((p["x"], p["y"], p["z"]), (q["x"], q["y"], q["z"])))
    xs = [p["x"] for p in hand]
    ys = [p["y"] for p in hand]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    out.extend([w, h, h / max(w, 1e-6)])
    return out


def extract_vector(hands, hands_count=None):
    """index.html の extractFeature と同じ並びのベクトルを返す。

    hands_count は「MediaPipeが検出した手の数」。収集時に3手を誤検出した
    サンプルが2件あり、そのときlandmarksは2手ぶんしか保存されていないため、
    保存済みの値を渡せるようにしてある（渡さなければ手の数から数える）。
    """
    items = [{"raw": lm, "norm": normalize_hand(lm)} for lm in hands[:2]]
    items.sort(key=lambda it: it["raw"][0]["x"])

    vector = [len(hands) if hands_count is None else hands_count]
    dummy_len = len(finger_features([{"x": 0.0, "y": 0.0, "z": 0.0}] * 21)) + 18
    for i in range(2):
        if i < len(items):
            vector.append(1)
            vector.extend(finger_features(items[i]["norm"]))
            for idx in KEY_POINTS:
                p = items[i]["norm"][idx]
                vector.extend([p["x"], p["y"], p["z"]])
        else:
            vector.append(0)
            vector.extend([0.0] * dummy_len)

    if len(items) >= 2:
        a, b = items[0]["raw"], items[1]["raw"]

        def dist(ia, ib):
            return math.dist(
                (a[ia]["x"], a[ia]["y"], a[ia].get("z", 0.0)),
                (b[ib]["x"], b[ib]["y"], b[ib].get("z", 0.0)),
            )

        cax = sum(p["x"] for p in a) / len(a)
        cay = sum(p["y"] for p in a) / len(a)
        cbx = sum(p["x"] for p in b) / len(b)
        cby = sum(p["y"] for p in b) / len(b)
        vector.extend([
            dist(0, 0), dist(8, 8), dist(12, 12), dist(4, 4), dist(20, 20),
            cbx - cax, cby - cay, abs(cbx - cax), abs(cby - cay),
        ])
    else:
        vector.extend([0.0] * 9)
    return vector


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verify = "--verify" in sys.argv
    if len(args) != 2:
        raise SystemExit(f"usage: python {sys.argv[0]} <生データ.json> <出力先.json> [--verify]")
    src, dst = args

    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    samples = data.get("samples") or []
    if not samples or "landmarks" not in samples[0]:
        raise SystemExit(f"{src} に landmarks がありません（生データを指定してください）")

    if verify:
        # 補正なしで計算し、元のvectorと一致するか（＝移植が正しいか）を確かめる
        worst = 0.0
        for s in samples:
            got = extract_vector(s["landmarks"], s["handsCount"])
            worst = max(worst, max(abs(a - b) for a, b in zip(got, s["vector"])))
        print(f"移植の検証: 元のvectorとの最大差 {worst:.3e}")
        if worst > 1e-9:
            raise SystemExit("一致しません。移植が誤っています")
        print("→ 一致。移植は正しい")
        return

    out = {
        "app": data.get("app"),
        "version": data.get("version"),
        "exportedAt": data.get("exportedAt"),
        "aspectCorrected": True,
        "trainAspect": TRAIN_ASPECT,
        "note": (
            "y を縦横比で割った等方座標で特徴量を作り直したもの。"
            "landmarksは除き、vectorは小数5桁。生データは dataset/ を参照（git管理外）"
        ),
        "signs": data.get("signs"),
        "samples": [],
    }
    for s in samples:
        hands = to_isotropic(s["landmarks"], TRAIN_ASPECT)
        out["samples"].append({
            "label": s["label"],
            "handsCount": s["handsCount"],
            "handedness": s["handedness"],
            "vector": [round(v, 5) for v in extract_vector(hands, s["handsCount"])],
        })

    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(
        f"{dst} を作成 / {len(out['samples'])} サンプル / "
        f"{os.path.getsize(dst) / 1048576:.2f} MB / 縦横比補正 {TRAIN_ASPECT:.4f}"
    )


if __name__ == "__main__":
    main()
