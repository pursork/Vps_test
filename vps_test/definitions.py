from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestDefinition:
    index: int
    name: str
    command: str
    source_url: str
    filename_hint: str
    kind: str = "script"


TEST_DEFINITIONS = [
    TestDefinition(1, "NodeQuality", "bash <(curl -sL https://run.NodeQuality.com)", "https://run.NodeQuality.com", "01_nodequality.sh"),
    TestDefinition(2, "ecs", "curl -L https://gitlab.com/spiritysdx/za/-/raw/main/ecs.sh -o ecs.sh && chmod +x ecs.sh && bash ecs.sh", "https://gitlab.com/spiritysdx/za/-/raw/main/ecs.sh", "02_ecs.sh"),
    TestDefinition(3, "unlock_media_short", "bash <(curl -L -s check.unlock.media)", "https://raw.githubusercontent.com/lmc999/RegionRestrictionCheck/main/check.sh", "03_check_unlock_media.sh"),
    TestDefinition(4, "tiktok", "bash <(curl -s https://raw.githubusercontent.com/lmc999/TikTokCheck/main/tiktok.sh)", "https://raw.githubusercontent.com/lmc999/TikTokCheck/main/tiktok.sh", "04_tiktok.sh"),
    TestDefinition(5, "yeahwu_check", "wget -qO- https://github.com/yeahwu/check/raw/main/check.sh | bash", "https://github.com/yeahwu/check/raw/main/check.sh", "05_yeahwu_check.sh"),
    TestDefinition(6, "media_check_place", "bash <(curl -sL Media.Check.Place)", "https://Media.Check.Place", "06_media_check_place.sh"),
    TestDefinition(7, "region_restriction_1_stream", "bash <(curl -L -s https://github.com/1-stream/RegionRestrictionCheck/raw/main/check.sh)", "https://github.com/1-stream/RegionRestrictionCheck/raw/main/check.sh", "07_region_restriction_1_stream.sh"),
    TestDefinition(8, "ip_check_place", "bash <(curl -sL IP.Check.Place)", "https://IP.Check.Place", "08_ip_check_place.sh"),
    TestDefinition(9, "netflix_verify_binary", "wget -O nf https://github.com/sjlleo/netflix-verify/releases/download/v3.1.0/nf_linux_amd64 && chmod +x nf && ./nf", "https://github.com/sjlleo/netflix-verify/releases/download/v3.1.0/nf_linux_amd64", "09_nf_linux_amd64", "binary"),
    TestDefinition(10, "bench", "wget -qO- bench.sh | bash", "https://bench.sh", "10_bench.sh"),
    TestDefinition(11, "backtrace_install", "curl https://raw.githubusercontent.com/ludashi2020/backtrace/main/install.sh -sSf | sh", "https://raw.githubusercontent.com/ludashi2020/backtrace/main/install.sh", "11_backtrace_install.sh"),
    TestDefinition(12, "auto_trace", "wget -N --no-check-certificate https://raw.githubusercontent.com/Chennhaoo/Shell_Bash/master/AutoTrace.sh && chmod +x AutoTrace.sh && bash AutoTrace.sh", "https://raw.githubusercontent.com/Chennhaoo/Shell_Bash/master/AutoTrace.sh", "12_autotrace.sh"),
    TestDefinition(13, "taier", "bash <(curl -sL res.yserver.ink/taier.sh)", "https://res.yserver.ink/taier.sh", "13_taier.sh"),
    TestDefinition(14, "nws", "wget -qO- nws.sh | bash", "https://nws.sh", "14_nws.sh"),
    TestDefinition(15, "bash_icu_speedtest", "bash <(curl -sL bash.icu/speedtest)", "https://raw.githubusercontent.com/i-abc/Speedtest/main/speedtest.sh", "15_bash_icu_speedtest.sh"),
    TestDefinition(16, "chatgpt", "wget -O chat.sh https://raw.githubusercontent.com/Netflixxp/chatGPT/main/chat.sh && chmod +x chat.sh && clear && ./chat.sh", "https://raw.githubusercontent.com/Netflixxp/chatGPT/main/chat.sh", "16_chatgpt.sh"),
]
