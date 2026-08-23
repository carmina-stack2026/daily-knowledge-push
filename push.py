import json
import random
import os
import requests
from datetime import datetime

# 配置
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
CONTENT_FILE = "content.json"
HISTORY_FILE = "history.json"

# 类别图标
CAT_ICONS = {
    "fable": "📖",
    "myth": "⚡", 
    "classic": "📚",
    "history": "🏛️",
    "custom": "🎎"
}

CAT_NAMES = {
    "fable": "寓言",
    "myth": "神话",
    "classic": "名著",
    "history": "历史",
    "custom": "习俗"
}

def load_json(filepath):
    """加载 JSON 文件"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filepath, data):
    """保存 JSON 文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def select_content():
    """选择一条未推送的内容"""
    library = load_json(CONTENT_FILE)
    history = load_json(HISTORY_FILE)

    # 获取已推送的 ID 列表
    seen_ids = set(h.get("id") for h in history)

    # 过滤未推送的内容
    available = [item for item in library if item["id"] not in seen_ids]

    # 如果全部看完，自动重置
    if not available:
        print("🔄 所有内容已看完，自动重置历史记录！")
        history = []
        available = library

    # 随机选择一条
    content = random.choice(available)

    # 记录到历史
    history.append({
        "id": content["id"],
        "title": content["title"],
        "category": content["category"],
        "date": datetime.now().strftime("%Y-%m-%d")
    })

    save_json(HISTORY_FILE, history)
    print(f"✅ 已选择：{content['title']} ({CAT_NAMES[content['category']]})")
    print(f"📊 已推送 {len(history)}/{len(library)} 条")

    return content

def format_markdown(content):
    """格式化为企业微信 Markdown"""
    cat = content["category"]
    icon = CAT_ICONS[cat]
    name = CAT_NAMES[cat]

    md = f"## {icon} 每日推送 · {name}\n\n"
    md += f"### {content['title']}\n\n"
    md += f"{content['content']}\n\n"
    md += "---\n\n"

    if content.get("moral"):
        md += f"💡 **启示：** {content['moral']}\n\n"

    md += f"📖 *来源：{content.get('source', '未知')}*\n"
    md += f"🏷️ *标签：{', '.join(content.get('tags', []))}*"

    return md

def push_to_wechat(content):
    """推送到企业微信机器人"""
    if not WEBHOOK_URL:
        print("❌ 未配置 WEBHOOK_URL，跳过推送")
        return False

    markdown = format_markdown(content)

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": markdown}
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()

        if result.get("errcode") == 0:
            print("💬 企业微信推送成功！")
            return True
        else:
            print(f"❌ 企业微信返回错误：{result}")
            return False
    except Exception as e:
        print(f"❌ 推送失败：{e}")
        return False

def main():
    print("=" * 50)
    print("📖 每日知识推送系统")
    print("=" * 50)
    print(f"⏰ 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 选择内容
    content = select_content()

    # 推送到微信
    success = push_to_wechat(content)

    if success:
        print("✅ 今日推送完成！")
    else:
        print("⚠️ 推送遇到问题，但历史记录已更新")

    print("=" * 50)

if __name__ == "__main__":
    main()
