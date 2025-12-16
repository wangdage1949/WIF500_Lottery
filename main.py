import itertools
import base58
import time
import os
import json
import signal
import sys

# ================== 配置区域 ==================

# 已知 WIF 开头部分（含占位符）
TEMPLATE_WIF = "K???????????5bCRZhiS5sEGMpmcRZdpAhmWLRfMmutGmPHtjVob"

# Base58 字符表
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# 不确定位置（从 1 开始计数）
POSITION_CANDIDATES = {
    1: "KL",  # 第1位只能是 K 或 L
    **{pos: ALPHABET for pos in range(2, 13)}  # 第2~12位，Base58全集
}

PROGRESS_FILE = "wif_recovery_progress.json"


# ================== 工具函数 ==================

def wif_to_privkey(wif: str):
    raw = base58.b58decode_check(wif)
    if raw[0] != 0x80:
        raise ValueError("不是主网 WIF")
    payload = raw[1:]
    if len(payload) == 32:
        return payload, False
    elif len(payload) == 33 and payload[-1] == 0x01:
        return payload[:-1], True
    else:
        raise ValueError("WIF 长度异常")


def generate_candidates_safe(template: str, index_cand_map: dict):
    chars = list(template)
    length = len(chars)

    positions = []
    for idx in range(length):
        if idx in index_cand_map:
            allowed = [c for c in index_cand_map[idx] if c in ALPHABET]
            positions.append((idx, allowed))
        else:
            positions.append((idx, [chars[idx]]))

    def generate_combinations(pos_index, current):
        if pos_index == len(positions):
            yield "".join(current)
            return
        idx, choices = positions[pos_index]
        for choice in choices:
            current[idx] = choice
            yield from generate_combinations(pos_index + 1, current)

    current = [None] * length
    yield from generate_combinations(0, current)


def save_progress(tested_count, total_candidates, found_wifs):
    data = {
        "tested_count": tested_count,
        "total_candidates": total_candidates,
        "found_wifs": found_wifs,
        "timestamp": time.time()
    }
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"\n保存失败: {e}")


def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return None
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取进度失败: {e}")
        return None


def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}分钟"
    else:
        return f"{seconds / 3600:.1f}小时"


def calculate_total_combinations(template, index_cand_map):
    total = 1
    for idx in range(len(template)):
        if idx in index_cand_map:
            total *= len([c for c in index_cand_map[idx] if c in ALPHABET])
    return total


# ================== 主逻辑 ==================

def main():
    print("WIF 恢复工具 v2（含字符组合规则约束）")
    print("=" * 60)
    print(f"模板 WIF : {TEMPLATE_WIF}")
    print(f"长度      : {len(TEMPLATE_WIF)}")

    index_cand = {}
    for pos, cand_str in POSITION_CANDIDATES.items():
        idx = pos - 1
        if idx < 0 or idx >= len(TEMPLATE_WIF):
            continue
        index_cand[idx] = cand_str

    total_candidates = calculate_total_combinations(TEMPLATE_WIF, index_cand)
    print(f"\n理论组合数（未过滤）≈ {total_candidates:,}")

    progress = load_progress()
    if progress:
        choice = input("\n检测到进度文件，是否继续？(y/n): ").lower().strip()
        if choice == 'y':
            tested = progress['tested_count']
            found = progress['found_wifs']
        else:
            tested = 0
            found = []
    else:
        tested = 0
        found = []

    start_time = time.time()
    last_save_time = start_time
    last_print = start_time

    def signal_handler(sig, frame):
        print("\n中断，保存进度中...")
        save_progress(tested, total_candidates, found)
        print("进度已保存，退出。")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("\n开始扫描（Ctrl+C 可随时中断）")

    try:
        candidate_generator = generate_candidates_safe(TEMPLATE_WIF, index_cand)

        for i, wif in enumerate(candidate_generator):
            if i < tested:
                continue
            tested = i + 1

            # ====== 添加组合规则过滤：第2~12位需包含大写+小写+数字 ======
            segment = wif[1:12]
            if not (
                any(c.isdigit() for c in segment) and
                any(c.islower() for c in segment) and
                any(c.isupper() for c in segment)
            ):
                continue  # 不符合组合要求

            now = time.time()
            if now - last_print >= 0.5 or tested == total_candidates:
                pct = tested / total_candidates
                elapsed = now - start_time
                speed = tested / elapsed if elapsed > 0 else 0
                remain = (total_candidates - tested) / speed if speed > 0 else 0
                bar = "#" * int(pct * 30)
                print(f"\r[{bar:<30}] {pct*100:6.2f}% "
                      f"{tested:,}/{total_candidates:,} 速度: {speed:,.0f}/s 剩余: {format_time(remain)}",
                      end='', flush=True)
                last_print = now

            if now - last_save_time >= 30 or tested % 10000 == 0:
                save_progress(tested, total_candidates, found)
                last_save_time = now

            try:
                priv_bytes, compressed = wif_to_privkey(wif)
            except Exception:
                continue

            print(f"\n\n✅ 找到合法 WIF！")
            print(f"  WIF: {wif}")
            print(f"  私钥: {priv_bytes.hex()}")
            print(f"  压缩: {compressed}")
            found.append((wif, priv_bytes.hex(), compressed))
            save_progress(tested, total_candidates, found)

        print("\n\n扫描完成!")
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("异常发生，保存进度...")
        save_progress(tested, total_candidates, found)

    print(f"\n共找到合法 WIF: {len(found)} 条")
    for i, (wif, priv_hex, compressed) in enumerate(found, 1):
        print(f"\n{i}. {wif}\n   私钥: {priv_hex}\n   压缩: {compressed}")


if __name__ == "__main__":
    main()
