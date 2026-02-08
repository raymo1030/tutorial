from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

SCHEDULE_FILE = Path(__file__).parent / "schedule.json"


def load_schedule() -> List[Dict[str, Any]]:
    """schedule.json から予定を読み込む。存在しない・壊れている場合は空リストを返す。"""
    if not SCHEDULE_FILE.exists():
        return []
    try:
        with SCHEDULE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # 最低限のバリデーション
            cleaned: List[Dict[str, Any]] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                if not title:
                    continue
                try:
                    priority = int(item.get("priority", 1))
                except (TypeError, ValueError):
                    priority = 1
                priority = max(1, min(3, priority))
                created_at = str(item.get("created_at") or "")
                if not created_at:
                    created_at = datetime.now().isoformat(timespec="seconds")
                cleaned.append(
                    {
                        "title": title,
                        "priority": priority,
                        "created_at": created_at,
                    }
                )
            return cleaned
        return []
    except (OSError, json.JSONDecodeError):
        # 壊れている場合は新規として扱う
        return []


def save_schedule(items: List[Dict[str, Any]]) -> None:
    """予定リストを schedule.json に保存する。"""
    with SCHEDULE_FILE.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def sort_by_priority(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """重要度の高い順（3→1）、同じ場合は作成日時の古い順に並び替える。"""
    return sorted(
        items,
        key=lambda x: (-int(x.get("priority", 1)), x.get("created_at", "")),
    )


def print_schedule(items: List[Dict[str, Any]]) -> None:
    """予定一覧をきれいに表示する。"""
    if not items:
        print("現在登録されている予定はありません。")
        return

    print("\n現在の予定（重要度の高い順）:")
    print("-" * 40)
    for idx, item in enumerate(items, start=1):
        title = str(item.get("title", ""))
        priority = int(item.get("priority", 1))
        created_at = str(item.get("created_at", ""))
        # created_at が ISO 形式なら日付部分だけ抜き出す
        created_date = created_at.split("T")[0] if "T" in created_at else created_at
        print(f"{idx}. [重要度: {priority}] {title} (登録日: {created_date})")
    print("-" * 40)


def input_new_items(existing: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """ユーザーから予定と重要度(1-3)を入力してリストに追加する。"""
    items = list(existing)

    print("\n新しい予定を追加します。")
    print("何も入力せずに Enter を押すと終了します。")

    while True:
        title = input("\n予定を入力してください: ").strip()
        if not title:
            break

        while True:
            priority_str = input("重要度を入力してください (1-3, 3が最重要): ").strip()
            try:
                priority = int(priority_str)
            except ValueError:
                print("数字で 1〜3 の範囲で入力してください。")
                continue
            if priority not in (1, 2, 3):
                print("重要度は 1, 2, 3 のいずれかで入力してください。")
                continue
            break

        items.append(
            {
                "title": title,
                "priority": priority,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    return items


def main() -> None:
    """今日の日付を表示し、予定と重要度を管理するシンプルな ToDo リスト。"""
    today = date.today()
    print(f"今日の日付: {today.strftime('%Y-%m-%d')}")

    # 既存の予定を読み込み
    items = load_schedule()
    items = sort_by_priority(items)
    print_schedule(items)

    # 新規入力
    items = input_new_items(items)

    # 並び替えて保存
    items = sort_by_priority(items)
    save_schedule(items)

    # 最終的な一覧を表示
    print("\n保存後の予定一覧:")
    print_schedule(items)


if __name__ == "__main__":
    main()
