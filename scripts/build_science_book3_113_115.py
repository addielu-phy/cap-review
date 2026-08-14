#!/usr/bin/env python
"""Build the curated 113-115 CAP science Book 3 physics/chemistry quiz."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "science" / "book3"

# Only questions whose required solving concepts stay inside Grade 8 semester 1
# (Book 3).  Entries were checked against the official question crops.
SELECTED = [
    (113, 4, "第6章 物質的基本結構", "元素週期表可讀出原子序、相對原子質量與同族關係，但不能告訴我們元素在自然界中的含量，所以答案是 C。"),
    (113, 18, "第3章 波動與聲音", "力學波必須依靠介質傳播；報導指出重力波不需要介質，電磁波也不需要介質，因此兩者都不屬於力學波，答案是 C。"),
    (113, 27, "第5章 溫度與熱", "冰從 −20°C 受熱，先升溫到 0°C；t₁ 到 t₂ 的平台是熔化過程，固態冰與液態水共存。故 T₁＝0°C，答案是 A。"),
    (113, 32, "第2章 物質的世界", "要由泳池中的安賽蜜濃度換算尿液體積，還需要知道尿液中安賽蜜的平均濃度，才能用溶質總量相等建立比例，答案是 D。"),
    (113, 36, "第4章 光", "物體位在凸透鏡焦點時，折射後光線互相平行。選項 B 顯示 P 到透鏡為 10 cm 且出射光平行，因此焦距可為 10 cm。"),
    (113, 46, "第1章 基本測量與科學探究", "圖中2021年住宅用電為52729億度；1億＝10⁸，所以52729×10⁸＝5.2729×10¹²度，答案是 D。"),
    (114, 1, "第3章 波動與聲音", "超聲波的頻率高於人耳可聽範圍，所以孕婦聽不見；關鍵是頻率太高，不是波速太快，答案是 C。"),
    (114, 2, "第1章 基本測量與科學探究", "密度＝質量÷體積。不規則石頭要用天平量質量，再用量筒排水法量體積，因此選甲與丙，答案是 B。"),
    (114, 4, "第6章 物質的基本結構", "笑氣是化合物，含氮、氧兩種原子；硫磺是元素，只含硫原子。因此笑氣所含原子種類比硫磺多，答案是 A。"),
    (114, 11, "第2章 物質的世界", "1000 g＝1,000,000 mg，30 mg／1,000,000 mg＝30 ppm；ppm 表示百萬分之一，答案是 C。"),
    (114, 14, "第4章 光", "紅光下呈黑色的球不反射紅光，因此白光下不可能是能反射各色光的白球；三球中最多只有另外兩球可能是白球，答案是 C。"),
    (114, 17, "第6章 物質的基本結構", "Ca²⁺的質子數 w＝20、電子數 y＝18；Cl⁻的質子數 x＝17、電子數 z＝18。只有 w＞z 正確，答案是 A。"),
    (114, 26, "第5章 溫度與熱", "比較比熱要控制質量與吸收熱量相同；由 Q＝mcΔT，溫度上升較快者比熱較小，所以答案是 D。"),
    (114, 29, "第2章 物質的世界", "X 在下層，表示密度比 Y 大。丙含 X 最多、乙含 X 最少，所以總質量 m丙＞m甲＞m乙，答案是 D。"),
    (114, 40, "第5章 溫度與熱", "冰塊使瓶內水蒸氣凝結，瓶內氣壓降低，水便能在較低壓力下再次汽化、沸騰並達到新平衡，答案是 A。"),
    (115, 1, "第1章 基本測量與科學探究", "指針偏左表示左側力矩較大；把左側校準螺絲向內旋入可減小左側力矩，使指針回到中央，答案是 A。"),
    (115, 2, "第6章 物質的基本結構", "題幹描述的物質可拉成細絲、壓成薄箔，且能導電，都是金屬的典型性質，因此屬於金屬元素，答案是 C。"),
    (115, 3, "第6章 物質的基本結構", "週期表同一族的元素具有相似的化學性質；第18族鈍氣不一定有相似物理性質，也不是雙原子分子，答案是 B。"),
    (115, 5, "第4章 光", "依反射角等於入射角，在方格上逐一作出反射路徑；T 射向 R 的反射光不會碰到上方牆壁，因此答案是 C。"),
    (115, 6, "第1章 基本測量與科學探究", "利用圖中的20 μm比例尺估算，灰色斑塊約為數十微米，與題圖所列10～30 μm的細胞尺度最接近，因此答案是 D。"),
    (115, 9, "第5章 溫度與熱", "潮濕空氣進入較冷室內後，水蒸氣碰到低溫磁磚而凝結成液態水珠，答案是 C。"),
    (115, 16, "第3章 波動與聲音", "分貝（dB）表示聲音的響度等級，最能回答「鼾聲很大嗎」；70 dB 是與問題相符的量測結果，答案是 A。"),
    (115, 18, "第1章 基本測量與科學探究", "排水法適合不溶於水、也不與水反應且能完全浸入的物體。銅片符合；鉀會與水反應，食鹽與葡萄糖會溶解，答案是 A。"),
    (115, 30, "第5章 溫度與熱", "三金屬塊質量相等且吸收熱量相同，比熱與升溫量成反比。甲、乙升溫相同且都比丙多，所以 S甲＝S乙＜S丙，答案是 A。"),
    (115, 36, "第2章 物質的世界", "甲的重量百分率為 20／(20＋20)＝50%；乙為 30／(30＋20)＝60%，兩者比為 50：60＝5：6，答案是 D。"),
]

# A few official per-question crops omit a shared chart/stem. These curated crops
# keep the complete context without dragging neighboring questions into the card.
PRIMARY_OVERRIDES = {
    (113, 46): "assets/113-q046.jpg",
}


def load_quiz(year: int) -> dict:
    text = (ROOT / "science" / str(year) / "data.js").read_text(encoding="utf-8")
    match = re.search(r"window\.QUIZ\s*=\s*(\{.*\})\s*;\s*$", text, re.S)
    if not match:
        raise ValueError(f"science/{year}/data.js does not contain window.QUIZ JSON")
    return json.loads(match.group(1))


def relative_asset(year: int, rel: str) -> str:
    return f"../{year}/{rel}"


def build() -> dict:
    sources = {year: load_quiz(year) for year in {year for year, *_ in SELECTED}}
    questions = []
    for seq, (year, source_no, unit, explanation) in enumerate(SELECTED, start=1):
        source = sources[year]["questions"][source_no - 1]
        if source["no"] != source_no:
            raise ValueError(f"{year} source index mismatch for question {source_no}")
        questions.append(
            {
                "no": seq,
                "displayNo": f"{year}-{source_no}",
                "sourceYear": year,
                "sourceNo": source_no,
                "unit": unit,
                "answer": source["answer"],
                "options": source.get("options", ["A", "B", "C", "D"]),
                "images": [PRIMARY_OVERRIDES[(year, source_no)]] if (year, source_no) in PRIMARY_OVERRIDES else [relative_asset(year, rel) for rel in source.get("images", [])],
                "prompt": source.get("prompt", ""),
                "explanation": explanation,
            }
        )

    counts = Counter(question["unit"] for question in questions)
    quiz = {
        "id": "cap-113-115-science-book3",
        "siteTitle": "會考複習自學平台",
        "title": "113–115年自然會考｜第三冊理化精選25題",
        "subject": "國二上理化（第三冊）",
        "grade": "國二上學期",
        "scoreScale": "percent",
        "perScore": 4,
        "totalScore": 100,
        "practiceCount": 10,
        "scoreNote": "完整測驗共25題、每題4分；隨手練習每回隨機抽10題並立即看詳解。",
        "sourceLabel": "113、114、115年國中教育會考自然科官方公開試題與參考答案",
        "sourceUrl": "https://cap.rcpet.edu.tw/examination.html",
        "description": "嚴格依國二上第三冊範圍選題，涵蓋基本測量、物質的世界、波動與聲音、光、溫度與熱、物質基本結構；保留官方原題截圖、自動評分、錯題練習與教師端雲端統計。",
        "scopeAudit": {
            "rule": "完整作答所需概念均在國二上第三冊；排除國二下化學反應、酸鹼與有機，國三力電、地科、天文及國一生物。",
            "sourceYears": dict(Counter(str(year) for year, *_ in SELECTED)),
            "chapterCounts": dict(counts),
            "selected": [{"year": y, "sourceNo": n, "unit": u} for y, n, u, _ in SELECTED],
        },
        "questions": questions,
    }
    return quiz


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    quiz = build()
    data = "/* Generated by scripts/build_science_book3_113_115.py. */\n"
    data += 'window.CLOUD = window.CLOUD || { enabled: false, teacherEmail: "", config: {} };\n'
    data += "window.QUIZ = " + json.dumps(quiz, ensure_ascii=False, indent=2) + ";\n"
    (OUT / "data.js").write_text(data, encoding="utf-8")
    print(json.dumps({"questions": len(quiz["questions"]), "chapters": quiz["scopeAudit"]["chapterCounts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
