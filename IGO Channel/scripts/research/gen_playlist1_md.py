import sys
sys.path.insert(0, "scripts/research")
from diagram import render

BASE = "B:Q16 W:R14"

def num(seq):
    toks = seq.split()
    out = []
    for i, t in enumerate(toks, 1):
        c, _, m = t.rpartition(":")
        who = "黒" if c == "B" else "白"
        out.append(f"{i}.{who}{'手抜き' if m == 'pass' else m}")
    return " → ".join(out)

E = []  # (section, no, id, title, status, freq, seq, sources(list of (tag, ok, note)), mistakes, memo)

def add(**k): E.append(k)

add(sec="1-A ハサミ", no=1, id="hoshi_kk_ikken_takabasami", title="一間高バサミ（黒Q12）", status="🟡",
    freq="約3%", seq="B:Q12 W:P14 B:O17 W:S16 B:R13",
    src=[("OGS","✓","白の応手 P14(トビ)/R17(三々) が IDEAL。主手順は上図"),
         ("GJ","✓","白の候補として R17・P14 を掲載（手順の続きは未掲載）"),
         ("IB","△","2.白P14 は一致。3手目を O16 とする図で、以降が OGS と異なる"),
         ("SL","✓","「厳しいハサミ。応手が必要で戦いになりやすい」")],
    mis=["（要調査）3手目以降がソース間で食い違うため、動画化前に追加ソースで確認する"],
    memo="白の三々入り（2.白R17）を選んだ場合は #2 と同型の手順になる（OGS）。")

add(sec="1-A ハサミ", no=2, id="hoshi_kk_ikken_hikubasami_sansan", title="一間低バサミ（黒R12）→ 白の三々入り", status="✅",
    freq="約22%（ハサミで最多）", seq="B:R12 W:R17 B:R16 W:Q17 B:P16 W:S16 B:S15 W:S17 B:R15 W:O17",
    src=[("OGS","✓","同じ手順。6.白S16 は「多数派」と注記。6.白O18 で止める型も定石"),
         ("IB","✓","10手目まで完全に一致（「ここまでが定石」）"),
         ("PN","✓","「白3と三々に入り、以下白11まで」。手数・要所（黒6のノビ、白7・9のハネツギ）が一致"),
         ("GJ","✓","三間高バサミの三々入りで同じ型（ハサミ側から押さえる）")],
    mis=["**押さえる向き**：3.黒Q17（上辺側）から押さえるのは、上辺に黒石があるときだけ。何もないときはハサミ側の R16 から押さえる（IB「こちらのオサエは◯のあたりに黒石が必要」、PN 定石2・図16、GJ「オサエる方向を間違えると…黒不利」、OGS は二間低バサミの同じ局面で Q17 を MISTAKE 判定）",
         "**5手目のハネ**：5.黒P16 のノビではなく P17 とハネるのは危険（PN「黒6とノビるのが定石。ここで黒6とハネるのは…危険」、OGS「P17 と S17 はよくある初心者の間違い」）",
         "**白の手順省略**：白が 6・8 のハネツギを省いて、すぐ O17 にトビ出すと黒に出切られて白が不利（PN 図5〜6）"],
    memo="シリーズの看板回。「三々入りされたら、どっちから押さえる？」はサムネ・Shorts 向き。")

add(sec="1-A ハサミ", no=3, id="hoshi_kk_nikentakabasami", title="二間高バサミ（黒Q11）", status="🟡",
    freq="約9%", seq="B:Q11 W:R17 B:R16 W:Q17 B:P16 W:O18",
    src=[("OGS","✓","白の IDEAL 応手が O17（両ガカリ）・R9・P14・O16・R17 と多い。三々入りは上図"),
         ("GJ","✓","白の候補 R17・O17・P14・P12"),
         ("IB","△","三々入りの図はあるが、押さえる向きが OGS と逆（Q17）で前提の配置が不明"),
         ("SL","✓","「模様を作る・崩すときのハサミ。ゆるいので味が残る」")],
    mis=["（要調査）IB と OGS で押さえる向きが逆。配置の違いかどうかを確認する"],
    memo="白の応手が多いので、前後編に分ける候補。")

add(sec="1-A ハサミ", no=4, id="hoshi_kk_nikenbasami", title="二間低バサミ（黒R11）", status="🟡",
    freq="約3%", seq="B:R11 W:R17 B:R16 W:Q17 B:P16 W:S16 B:S15 W:S17 B:R15 W:O17",
    src=[("OGS","✓","上の手順。押さえを 3.黒Q17 にするのは MISTAKE 判定"),
         ("GJ","✓","白の候補 R17・O17（手順の続きは未掲載）"),
         ("SL","✓","「上辺が大きく、右辺が小さいときに打つ」")],
    mis=["#2 と同じ（押さえる向き）"],
    memo="手順全体を確認できたのは OGS だけ。#2 と同じ型であることを動画で説明する。")

add(sec="1-A ハサミ", no=5, id="hoshi_kk_sangentakabasami", title="三間高バサミ（黒Q10）→ 白の三々入り", status="✅",
    freq="約2%", seq="B:Q10 W:R17 B:R16 W:Q17 B:P16 W:S16 B:S15 W:S17 B:S14 W:O17 B:R13",
    src=[("OGS","✓","上の手順（9.黒S14 は現代型）"),
         ("GJ","✓","8手目まで一致。9手目を R15（旧型）とし、黒Q14 で終わる"),
         ("SL","✓","ゆるいハサミで、局所的な結果は手抜きに近い")],
    mis=["GJ「オサエる方向を間違えると白にワラわれ、黒は実利を稼がれただけで勢力を築けず不利」",
         "9手目：OGS は S14 を現代型、R15 を旧定石と注記 → 「昔の定石 vs 今の定石」の比較ネタに使える"],
    memo="")

add(sec="1-A ハサミ", no=6, id="hoshi_kk_sangenbasami", title="三間低バサミ（黒R10）", status="🟡",
    freq="約1%", seq="B:R10 W:R17 B:R16 W:Q17 B:P16 W:S16 B:S15 W:S17 B:S14 W:O17 B:R13",
    src=[("OGS","✓","上の手順（出典：AlphaGo以降のプロ棋譜。例：譚笑 vs 陳耀燁 2018）"),
         ("GJ","✓","白の候補 R17・R16・O17"),
         ("SL","✓","星の石が勢力向きなら合うハサミ")],
    mis=["#5 と同じ"],
    memo="#5 とまとめて1本にする案もある。")

add(sec="1-B ツケ", no=7, id="hoshi_kk_tsuke_hane", title="ツケ（黒Q14）→ 白ハネ（Q13）＝ツケオサエ型", status="✅",
    freq="約2%", seq="B:Q14 W:Q13 B:R15 W:P14 B:Q15",
    src=[("OGS","✓","同じ手順。続きは 6.白P13 → 7.黒O16"),
         ("IB","✓","5手目まで一致し、6手目を P13・R13・S14 に分岐（「ツケにはハネよ」）"),
         ("SL","✓","Tsukeosae（ツケオサエ）として掲載。「何もない盤面では黒がわずかに損（B-0.2）」")],
    mis=["IB「この手で☆のアテは悪手。取れない石は追いかけてはいけない」（6.白S14 の変化）",
         "OGS：2.白Q13 の後の 黒P13 は TRICK（ハメ手）"],
    memo="アマに人気だが、AI評価はやや黒が損 → 「よく打つけど実は…」の切り口。")

add(sec="1-B ツケ", no=8, id="hoshi_kk_tsuke_nobi", title="ツケ（黒Q14）→ 白ノビ（R15）＝AI流", status="🟡",
    freq="—", seq="B:Q14 W:R15 B:Q15 W:R16 B:Q17 W:Q13 B:R17",
    src=[("OGS","✓","「R16 が新定石」。3.黒R16 は MISTAKE 判定"),
         ("SL","✓","Attach Extend として掲載"),
         ("IB","—","該当図なし")],
    mis=["3手目：OGS は R16 を MISTAKE、Q15 が正しいとする"],
    memo="3つ目のソースが必要。")

add(sec="1-B ツケ", no=9, id="hoshi_kk_kosumitsuke", title="コスミツケ（黒R15）", status="✅",
    freq="約7%", seq="B:R15 W:Q14 B:O16 W:R10",
    src=[("OGS","✓","上の手順（4.白R10 は「二立三析」の急所）"),
         ("IB","✓","3手目まで一致（黒の打つ場所は変わらない）。黒Q10 がある配置で解説"),
         ("SL","✓","Kick joseki。AI以前は黒が悪いとされたが、AI評価は B+0.2。2016年以降プロでも増加"),
         ("GJ","✓","候補手として掲載")],
    mis=["OGS：1.黒R15 の後の白 P14・S15・手抜きは MISTAKE（白は 2.Q14 のノビ）",
         "OGS：3.黒O16 のトビを省いて白に押さえられると黒が危ない"],
    memo="「昔は悪手、AIで復活」ネタ。")

add(sec="1-C 受け", no=10, id="hoshi_kk_kogeima_uke", title="小ケイマ受け（黒O17）基本型", status="✅",
    freq="約56%（最多）", seq="B:O17 W:S16 B:R17 W:R11",
    src=[("IB","✓","同じ手順（スベリ → 三々で受ける → 二間ビラキ）"),
         ("GJ","✓","2.白S16 → 3.黒R17、白のヒラキ R10・R11"),
         ("OGS","✓","2.白S16 に 3.黒R17 が IDEAL"),
         ("SL","✓","最も多い応手で、AIの評価も高い")],
    mis=["OGS：2.白S16（スベリ）は AI 評価でやや損とされ、プロでは減った → 次の #11 へつなげる"],
    memo="")

add(sec="1-C 受け", no=11, id="hoshi_kk_kogeima_uke_ai_tsuke", title="小ケイマ受け → 白の星下ツケ（R16）＝AI流", status="🟡",
    freq="—", seq="B:O17 W:R16 B:R17 W:S17 B:R18 W:Q15 B:S16 W:R15 B:S18",
    src=[("OGS","✓","「最も多い手。AIの影響でほぼすべてのプロが打っている」"),
         ("GJ","✓","候補（ツケ）として掲載。手順の続きは未掲載"),
         ("SL","✓","受けた後の白の選択肢として掲載")],
    mis=["OGS：2.白R16 の後の 黒Q17 は MISTAKE",
         "OGS：4.白S17 の後の 黒S16 は「よくある級位者の間違い」"],
    memo="手順全体を確認できたのは OGS だけ。")

add(sec="1-C 受け", no=12, id="hoshi_kk_ikken_uke", title="一間受け（黒O16）", status="🟡",
    freq="約29%", seq="B:O16 W:R17 B:R16 W:S16 B:Q17 W:S18 B:R18 W:S17",
    src=[("OGS","✓","受けた後の三々入りは上図（出典：大竹英雄 *Opening Theory Made Easy*）。AIはノゾキ P15 を好む"),
         ("GJ","✓","白の候補 S16・R16・R17・M17・R10・R11"),
         ("SL","✓","勢力重視。隅の地は持ちにくい")],
    mis=["（要調査）"],
    memo="IB の一間受けページは自動取得できなかったので、手で確認する。")

add(sec="1-C 受け", no=13, id="hoshi_kk_ogeima_uke", title="大ケイマ受け（黒N17）", status="🟡",
    freq="約3%", seq="B:N17 W:R17 B:R16 W:Q17 B:P16 W:P17 B:O17 W:S16 B:S15 W:S17 B:R15",
    src=[("OGS","✓","白の三々入りを誘う手（伝統型）"),
         ("GJ","✓","白の候補 R17・R16・L17"),
         ("SL","✓","「白に三々を与え、黒が外勢を取る」")],
    mis=["（要調査）"],
    memo="")

add(sec="1-D 手抜き", no=14, id="hoshi_kk_tenuki_sansan", title="手抜き → 白の三々入り", status="🟡",
    freq="手抜き全体で約20〜30%（AI以降）", seq="B:pass W:R17 B:Q17 W:R16 B:Q15",
    src=[("OGS","✓","出典：AlphaGo以降のプロ棋譜"),
         ("SL","✓","手抜きは AI が好む選択肢"),
         ("IB","—","「星-三々入り」ページで照合予定")],
    mis=["（要調査）"],
    memo="Playlist 2（ダイレクト三々）への橋渡し回。")

add(sec="1-D 手抜き", no=15, id="hoshi_kk_tenuki_ryogakari", title="手抜き → 白の両ガカリ（O17）", status="🟡",
    freq="—", seq="B:pass W:O17 B:Q14 W:Q13 B:P14 W:R17 B:R15 W:Q17 B:R13",
    src=[("IB","✓","上の手順（外ヅケ → ハネて三々）。「ツケられた石をハネて三々でサバく」。※上辺に黒石（L16）がある配置の図"),
         ("OGS","△","5.黒P14 まで一致。6手目が OGS は P13、IB は R17"),
         ("GJ","✓","両ガカリのページあり（初手のみ）")],
    mis=["OGS：両ガカリに 3.黒R15 は MISTAKE",
         "IB：ツケは強い方の石（周りに黒石がある側）にツケる"],
    memo="柳澤チャンネルの「両ガカリは怖くない！」が伸びている（需要あり）。")

add(sec="1-D 手抜き", no=16, id="hoshi_kk_tenuki_ikkentaka_ryogakari", title="手抜き → 白の一間高両ガカリ（O16）", status="🟡",
    freq="—", seq="B:pass W:O16 B:O15 W:N15 B:O14 W:N14 B:O13 W:N17",
    src=[("OGS","✓","3.黒O15 が普通。白N15 は伝統型、P15 は AlphaGo 型"),
         ("IB","△","別配置（黒Q11 あり）の図のみ"),
         ("GJ","—","")],
    mis=["OGS：4.白N15 の後の 黒P16 は MISTAKE"],
    memo="変化が複雑。後回しでよい。")

SRC_LEGEND = """| 略号 | ソース | 種類 |
|---|---|---|
| OGS | [OGS Joseki Explorer](https://online-go.com/joseki)（API `https://online-go.com/oje/position?id=<node>`） | 海外Web定石DB（手ごとに IDEAL / GOOD / MISTAKE / TRICK の判定と出典つき） |
| SL | [Sensei's Library: 4-4 point low approach](https://senseis.xmp.net/?44PointLowApproach) | 海外Wiki。頻度はWaltheriのプロ棋譜検索、AI評価はKaTrainによる |
| GJ | [囲碁定石研究（星への小ゲイマガカリ）](https://gojoseki.shogidb2.com/hoshi/kogeimagakari/) | 日本語の定石DB（定石名と候補手） |
| IB | [初心者〜初段までの囲碁定石](https://igobook.info/) | 日本語の解説サイト（SGF＋悪手の解説つき） |
| PN | [パンダネット 囲碁入門「星の定石－ハサミ」](https://www.pandanet.co.jp/igonyumon/11-02.htm) | 日本語の入門講座（間違いと咎め方の解説つき） |
| AI | KataGo | **未実施**（Homebrewでのビルドが、依存ライブラリ libzip のダウンロード失敗で止まっている） |"""

out = []
out.append("""# Playlist 1：星・小ケイマかかりへの応手（定石整理・検証表）

> 状態：**レビュー待ち**（2026-10-22 作成）。各定石は複数の公開ソースで手順を照合済み。AI評価（KataGo）は未実施。
> この表で ✅ になった定石から動画化する。

## 表記ルール

- 盤面は右上隅。**黒＝星（Q16）、白＝小ケイマかかり（R14）** に固定（座標は GTP 表記。列は I を飛ばす）
- 図の `X`＝黒の星、`O`＝白のかかり、`B1`・`W2`… が手順（黒・白と手番）
- ソース側の図の向き（上辺かかり等）は、すべてこの向きに変換してから照合した（`scripts/research/` のスクリプト）
- 頻度は SL 掲載のプロ棋譜統計（Waltheri、2021年取得）。全盤面の状況で大きく変わるので目安

## 判定

| 判定 | 意味 |
|---|---|
| ✅ | 3つ以上のソースで主手順が一致。小さい変化は注記 |
| 🟡 | 候補手は3ソースで一致するが、手順全体は1〜2ソースのみ、またはソース間で食い違いあり → 動画化前に追加確認 |

## ソース
""")
out.append(SRC_LEGEND + "\n")
out.append("""## 一覧

| # | 定石 | 判定 | プロでの頻度 |
|---|---|---|---|""")
for e in E:
    out.append(f"| {e['no']} | [{e['title']}](#{e['no']}-{e['id']}) | {e['status']} | {e['freq']} |")
out.append("| 17 | まとめ：星・小ケイマかかりの間違い10選 | — | 各回の「間違えやすい手」から選ぶ |\n")

sec = None
for e in E:
    if e["sec"] != sec:
        sec = e["sec"]; out.append(f"\n---\n\n## {sec}\n")
    out.append(f"### <a id=\"{e['no']}-{e['id']}\"></a>{e['no']}. {e['title']} {e['status']}\n")
    out.append(f"- id: `{e['id']}`　/　頻度: {e['freq']}")
    out.append(f"- 主手順: {num(e['seq'])}\n")
    out.append("```\n" + render(BASE, e["seq"]) + "\n```\n")
    out.append("| ソース | 一致 | メモ |\n|---|---|---|")
    for tag, ok, note in e["src"]:
        out.append(f"| {tag} | {ok} | {note} |")
    out.append("\n**間違えやすいポイント**\n")
    for m in e["mis"]:
        out.append(f"- {m}")
    if e["memo"]:
        out.append(f"\n> 動画メモ：{e['memo']}")
    out.append("\n- [ ] レビュー済み（自分）　- [ ] KataGo で目数損失を確認\n")

out.append("""---

## 次にやること

1. KataGo を導入して、✅ の定石から順に各手の目数損失を記録する（`sources/<id>.yaml` の `ai_check`）
2. 🟡 の定石は、日本語ソース（IB の該当ページの手動確認、GJ の棋譜DB、プロ棋士の解説動画）を追加して ✅ にする
3. 確定した手順を `joseki/<id>.sgf` に書き出す（動画生成パイプラインの入力になる）
""")
open("joseki/PLAYLIST1_hoshi_kogeima_kakari.md", "w").write("\n".join(out))
print("ok", len(E))
