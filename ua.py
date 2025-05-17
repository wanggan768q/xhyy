import random


def get_ua():
    # Base components
    chrome_majors = list(range(80, 116))
    chrome_minors = [0, 90, 100, 110]
    chrome_build_range = (1000, 5000)
    wechat_versions = [f"7.0.{i}.1781" for i in range(10, 31)] + [f"8.0.{i}.1781" for i in range(0, 11)]
    net_types = ["WIFI", "4G", "5G", "Ethernet"]
    mini_prog_env_versions = [f"Windows {i}.{j}.{k}" for i in range(1, 4) for j in range(0, 3) for k in range(0, 3)]
    winwechat_versions = f"WMPF {hex(random.randint(0x6000000, 0x7000000))[2:].upper()}"
    xweb_builds = list(range(7000, 9000))

    major = random.choice(chrome_majors)
    minor = random.choice(chrome_minors)
    build = random.randint(*chrome_build_range)
    patch = random.randint(0, 50)
    wechat = random.choice(wechat_versions)
    net = random.choice(net_types)
    mini_env = random.choice(mini_prog_env_versions)
    win_wmpf = winwechat_versions
    win_wechat_hex = hex(random.randint(0x6000000, 0x7000000))[2:].upper()
    xweb = random.choice(xweb_builds)

    ua = (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{major}.{minor}.{build}.{patch} Safari/537.36 "
        f"MicroMessenger/{wechat}(0x{win_wechat_hex}) "
        f"NetType/{net} MiniProgramEnv/{mini_env} "
        f"WindowsWechat/{win_wmpf} WindowsWechat(0x{win_wechat_hex}) "
        f"XWEB/{xweb}"
    )
    return ua


