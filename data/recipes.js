// 術のレシピ（index.html と tools/check_recipes.html の共通の情報源）
//
// レシピを足す・直すときは、必ず tools/check_recipes.html を開いて
// 衝突がないことを確認すること。2つの罠がある:
//   完全重複 … 別々の術が同じ並びだと区別できない
//   途中暴発 … 短いレシピが長いレシピの部分列だと先に発動してしまう
// 2印のレシピは構造的に暴発しやすいので基本的に避ける。

// ===== 転換2: 術を同時待ち受けする =====
// 「次の印を待つ」のをやめ、直近に確定した印の並びに対して全レシピを末尾一致させる。
// 順番待ちが消え、何の術を出すかを結び手が決められる。
//
// 出典: manga-funnyheaven.com / baike.baidu.com（ページによって食い違いあり）。
// 雷遁・雷切の「丑→卯→申」はよこぼ確認済みの正解（baiduの「申→卯→丑」は逆順で誤り）。
//
// この15本は事前に衝突チェック済み:
//   - 完全に同じ並びのレシピ: なし
//   - 長い術を結ぶ途中で短い術が暴発する組み合わせ: なし
// 追加するときは必ず再チェックすること。特に2印のレシピは暴発しやすい
// （外道・輪廻天生「未→巳」は分身の術「未→巳→寅」の途中で必ず暴発するため外した）。
// 水遁・黒雨は分身の術と完全に同一（未→巳→寅）だったため外した。
const JUTSU_RECIPES = [
  { id: "bunshin",   name: "分身の術",           signs: ["hitsuji", "mi", "tora"],                    element: "neutral" },
  { id: "henge",     name: "変身の術",           signs: ["inu", "i", "hitsuji"],                      element: "neutral" },
  { id: "raikiri",   name: "雷遁・雷切",         signs: ["ushi", "u", "saru"],                        element: "lightning" },
  { id: "haisekisho", name: "火遁・灰積焼",      signs: ["mi", "ne", "tora"],                         element: "fire" },
  { id: "rougane",   name: "氷遁・狼牙雪崩の術", signs: ["ne", "u", "inu"],                           element: "ice" },
  { id: "izanagi",   name: "イザナギ",           signs: ["u", "i", "hitsuji"],                        element: "neutral" },
  { id: "mokusatsu", name: "木遁・黙殺縛",       signs: ["tora", "inu", "mi"],                        element: "wood" },
  { id: "hakugeki",  name: "白激の術",           signs: ["mi", "ne", "tatsu"],                        element: "neutral" },
  { id: "doryudan",  name: "土遁・土龍弾",       signs: ["hitsuji", "uma", "tatsu", "tora"],          element: "earth" },
  { id: "ryuka",     name: "火遁・龍火の術",     signs: ["mi", "tatsu", "u", "tora"],                 element: "fire" },
  { id: "edotensei", name: "穢土転生",           signs: ["tora", "mi", "inu", "tatsu"],               element: "neutral" },
  { id: "kawara",    name: "忍法・瓦手裏剣",     signs: ["tora", "tatsu", "ne", "tora"],              element: "earth" },
  { id: "kuchiyose", name: "口寄せの術",         signs: ["i", "inu", "tori", "saru", "hitsuji"],      element: "neutral" },
  { id: "goukakyu",  name: "火遁・豪火球の術",   signs: ["mi", "hitsuji", "saru", "i", "uma", "tora"], element: "fire" },
  { id: "housenka",  name: "火遁・鳳仙火の術",   signs: ["ne", "tora", "inu", "ushi", "u", "tora"],   element: "fire" },

  // 全44印。原典で最長とされる術。ネタ枠。
  //
  // 元の並びには 21印目と41印目に「壬」が入っているが、壬は十干（みずのえ）で
  // 十二支ではない。このセンサーが認識できるのは子丑寅卯辰巳午未申酉戌亥の12種
  // だけなので、その2つを抜いた42印にしてある。正しい印が判明したら足すこと。
  //
  // 既存15種のどれもこの並びの途中には現れないことを確認済み（暴発なし）。
  { id: "suiryudan", name: "水遁・水龍弾の術",
    signs: [
      "ushi", "saru", "u", "ne", "i", "tori", "ushi", "uma", "tori", "ne",
      "tora", "inu", "tora", "mi", "ushi", "hitsuji", "mi", "i", "hitsuji", "ne",
      /* 壬 */ "saru", "tori", "tatsu", "tori", "ushi", "uma", "hitsuji", "tora", "mi", "ne",
      "saru", "u", "i", "tatsu", "hitsuji", "ne", "ushi", "saru", "tori",
      /* 壬 */ "ne", "i", "tori"
    ],
    element: "water" }
];

const ELEMENT_STYLE = {
  fire:      { label: "火", color: "#ff7a3c", glow: "#ffd166" },
  lightning: { label: "雷", color: "#7ae0ff", glow: "#ffffff" },
  ice:       { label: "氷", color: "#9fd8ff", glow: "#e8f7ff" },
  wood:      { label: "木", color: "#7fdc8a", glow: "#d4ffcf" },
  earth:     { label: "土", color: "#d0a066", glow: "#ffe1b0" },
  water:     { label: "水", color: "#5bc8ff", glow: "#d6f2ff" },
  neutral:   { label: "印", color: "#a9b4ff", glow: "#e6ebff" }
};

// ブラウザからもNode（もし使うなら）からも読めるようにしておく
if (typeof window !== "undefined") {
  window.JUTSU_RECIPES = JUTSU_RECIPES;
  window.ELEMENT_STYLE = ELEMENT_STYLE;
}
