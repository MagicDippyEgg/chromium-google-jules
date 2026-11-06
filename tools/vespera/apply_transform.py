import os
import sys
import shutil
import subprocess

def transform_dist(dist_dir):
    print(f"Transforming distribution at {dist_dir} into Vespera...")

    # 1. Replace logo PNGs in the root
    theme_dir = "chrome/app/theme/chromium"
    for size in ["16", "24", "32", "48", "64", "128", "256"]:
        src = os.path.join(theme_dir, f"product_logo_{size}.png")
        dst = os.path.join(dist_dir, f"product_logo_{size}.png")
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {src} -> {dst}")

    # 2. Update locales/*.pak cleanly
    locales_dir = os.path.join(dist_dir, "locales")
    if os.path.exists(locales_dir):
        tmp_unpacked = "/tmp/vespera_pak_unpack"
        for pak_name in os.listdir(locales_dir):
            if not pak_name.endswith(".pak"):
                continue
            pak_path = os.path.join(locales_dir, pak_name)
            if os.path.exists(tmp_unpacked):
                shutil.rmtree(tmp_unpacked)
            os.makedirs(tmp_unpacked, exist_ok=True)

            # Extract
            subprocess.run([sys.executable, "tools/grit/pak_util.py", "extract", pak_path, "-o", tmp_unpacked], check=True)

            # Replace strings in each extracted item preserving UTF-8
            for item in os.listdir(tmp_unpacked):
                ip = os.path.join(tmp_unpacked, item)
                with open(ip, "rb") as f:
                    content = f.read()

                # Replace product names
                new_content = content.replace(b"Google Chrome", b"Vespera")
                new_content = new_content.replace(b"Chromium", b"Vespera")
                new_content = new_content.replace(b"Chrome", b"Vespera")

                if new_content != content:
                    with open(ip, "wb") as f:
                        f.write(new_content)

            # Create updated pak
            repacked_pak = "/tmp/repacked_locale.pak"
            subprocess.run([sys.executable, "tools/grit/pak_util.py", "create", "-i", tmp_unpacked, repacked_pak], check=True)
            shutil.copy2(repacked_pak, pak_path)
            print(f"Transformed locale {pak_name}")

    # 3. Update chrome_100_percent.pak and chrome_200_percent.pak with Vespera logo
    for p_name in ["chrome_100_percent.pak", "chrome_200_percent.pak"]:
        p_path = os.path.join(dist_dir, p_name)
        if not os.path.exists(p_path):
            continue
        tmp_unpacked = "/tmp/vespera_chrome_pct"
        if os.path.exists(tmp_unpacked):
            shutil.rmtree(tmp_unpacked)
        os.makedirs(tmp_unpacked, exist_ok=True)
        subprocess.run([sys.executable, "tools/grit/pak_util.py", "extract", p_path, "-o", tmp_unpacked], check=True)

        # Replace PNG resources with Vespera logo
        logo_png = open("chrome/app/theme/chromium/product_logo_128.png", "rb").read()
        for item in os.listdir(tmp_unpacked):
            ip = os.path.join(tmp_unpacked, item)
            with open(ip, "rb") as f:
                d = f.read()
            if d.startswith(b"\x89PNG") and len(d) in [1399, 1545, 2172, 4393, 759]:
                with open(ip, "wb") as f:
                    f.write(logo_png)

        repacked = "/tmp/repacked_pct.pak"
        subprocess.run([sys.executable, "tools/grit/pak_util.py", "create", "-i", tmp_unpacked, repacked], check=True)
        shutil.copy2(repacked, p_path)
        print(f"Transformed {p_name}")

    # 4. Inject initial_preferences
    init_pref = os.path.join(dist_dir, "initial_preferences")
    with open(init_pref, "w") as f:
        f.write('{"homepage": "chrome://newtab", "homepage_is_newtabpage": true, "browser": {"show_home_button": true}}\n')
    master_pref = os.path.join(dist_dir, "master_preferences")
    shutil.copy2(init_pref, master_pref)

    print("Vespera transformation complete!")

if __name__ == "__main__":
    transform_dist(sys.argv[1])
