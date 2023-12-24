import argparse
import os
import shutil
import re
from pathlib import Path
import pip
import concurrent.futures
import urllib.request
import urllib.error
import zipfile

try:
    import demjson
except:
    package_name = "demjson"
    print(f"{package_name} 未安装")
    import pkg_resources
    version = pkg_resources.get_distribution("setuptools").version
    version = "68.2.2"
    pip.main(['install', 'setuptools==57.5.0'])
    pip.main(['install', package_name])

    print(f"{package_name} 安装完成")
finally:
    try:
        import demjson
    except:
        print(f"{package_name} 安装失败, 请手动安装")
        exit(2)
    # setuptools安装回原来的版本
    pip.main(['install', f'setuptools=={version}'])


BASE_DIR = Path(os.path.abspath(__file__)).parent # 项目根目录 

IFRAME_RE = re.compile('<iframe src="/wid.*?></iframe>')
IMAGE_RE = re.compile(r'!\[(.+?)\]\((assets\/.+?)\)')
BLACK_DIR_PATTERN = ("assets", '.vuepress')
BLACK_FILE_PATTERN = ("README.md", "sidebar.js", "config.js")

CONFIG_DICT = {}

if os.path.exists(f"{BASE_DIR}/.env"):
    with open(f"{BASE_DIR}/.env") as f:
        for line in f:
            k,v = line.split("=", 1)
            v = v.strip() 
            if not len(v):
                v = None
            if v is not None and v[0] in ('"', "'"):
                v = eval(v)
            print(f"--- {k} = {v}")
            CONFIG_DICT[k] = v

IMAGE_URL = CONFIG_DICT.get("IMAGE_URL")
DOCS_VAL = CONFIG_DICT.get("DOCS_VAL", 'docs')

SITE_TITLE = CONFIG_DICT.get("SITE_TITLE", None)
SITE_DESC = CONFIG_DICT.get("SITE_DESC", None)


def clean_file(fp):
    """
        1. 删除笔记中的挂件iframe
        2. 处理图片链接
    """
    if not os.path.exists(fp) or not os.path.isfile(fp):
        return
    print(f"正在处理 : {fp}")
    raw_text = Path(fp).read_text()

    raw_text = IFRAME_RE.sub("", raw_text)
    if IMAGE_URL is not None:
        raw_text = IMAGE_RE.sub(lambda match: f"![{match.group(1)}]({IMAGE_URL}{ match.group(2)})", raw_text)

    with open(fp, "w+") as f:
        f.write(raw_text)


def clean_dir(dir_path):
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return

    root, dirs, files = next(os.walk(dir_path))
    
    for file in files:
        if file in BLACK_FILE_PATTERN:
            continue
        full_path = os.path.join(root, file)
        clean_file(full_path)
    
    for dir in dirs:
        if dir.startswith(".") or dir in BLACK_DIR_PATTERN:
            continue
        full_path = os.path.join(root, dir)
        clean_dir(full_path)
    # 优先使用 README中内容 , 然后才是文件夹层级的内容, 都没有就创建一个空的README文件
    if "README.md" not in files:
        text = f"## {os.path.basename(dir_path)}"
        # assert os.path.exists(f"{dir_path}.md")
        if os.path.exists(f"{dir_path}.md"):
            text = Path(f"{dir_path}.md").read_text()
        with open(f"{dir_path}/README.md", "w+") as f:
            f.write(text)
    
    if os.path.exists(f"{dir_path}.md"):
        os.remove(f"{dir_path}.md")

def str_del_prefix(str_, prefix):
    return str_[len(prefix):]

def _gen_sidebar(dir_path, level):

    def gen_sidebar_item(path):
        bar =  {
            "title": os.path.basename(path),
            "path": str_del_prefix(path, str(BASE_DIR) + '/docs'),
        }
        
        if path[-3:] != '.md':
            bar["path"] = f"{bar['path']}/"
            bar["children"] = []
        else:
            bar["title"] = bar["title"][:-3]
            bar["path"] = bar["path"][:-3]
        
        return bar
    
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return

    bar = gen_sidebar_item(dir_path)

    root, dirs, files = next(os.walk(dir_path))

    for dir in dirs:
        if dir in BLACK_DIR_PATTERN:
            continue
        full_path = os.path.join(root, dir)
        bar["children"].append(_gen_sidebar(full_path, level + 1))

    for file in files:
        if file in BLACK_FILE_PATTERN:
            continue
        full_path = os.path.join(root, file)
        bar["children"].append(gen_sidebar_item(full_path))
    
    bar["children"] = sorted(bar["children"], key=lambda x: x['title'])

    to_replace = (
        ('"', "'"),
        ("True", "true"),
        ("False", "false"),
        ("'title'", "title"),
        ("'path'", "path"),
        ("'children'", "children"),
        ("'[", "["),
        ("]'", "]"),
        ("'{", "{"),
        ("}'", "}"),
    )

    resp_str = str(bar)
    for a, b in to_replace:
        resp_str = resp_str.replace(a, b)

    with open(f"{dir_path}/sidebar.js" , 'w+') as f:
        f.write(f"[{resp_str}]")

    return bar


def gen_config(dir):
    full_path = f"{BASE_DIR}/docs/{dir}"
    if not os.path.exists(full_path) or dir in BLACK_DIR_PATTERN:
        return
    config_file = f"{BASE_DIR}/docs/.vuepress/config.js"
    with open(config_file) as f:
        text = f.read()
        text = text.replace("module.exports =","")
    
    config = demjson.decode(text)

    if SITE_TITLE is not None:
        config["title"] = SITE_TITLE
    
    if SITE_DESC is not None:
        config["description"] = SITE_DESC

    _gen_config_nav(config, dir)
    _gen_config_sidebar(config, dir)

    op = "./test_aksdjklamzxncaksldasgd.js"
    demjson.encode_to_file('./test_aksdjklamzxncaksldasgd.js', config, compactly=False, overwrite=True)

    raw_text = Path(op).read_text()
    to_replace = (
        ('"[', '['),
        (']"', ']'),
    )
    for a,b in to_replace:
        raw_text = raw_text.replace(a,b)

    with open(config_file, 'w+') as f:
        f.write(f"module.exports = {raw_text}")
    
    os.remove(op)


def _gen_config_nav(config, dir):
    nav = config["themeConfig"]["nav"]
    for item in nav:
        if item['text'] == DOCS_VAL:
            nav_docs = item
            need_push = False
            break
    else:
        nav_docs, need_push = {"text": DOCS_VAL, "items":[]}, True
    for item in nav_docs['items']:
        if item['text'] == dir:
            item['link'] = f"/{dir}/"
            break
    else:
        nav_docs['items'].append({
            "text": dir,
            "link": f"/{dir}/"
        })

    if need_push:
        nav.append(nav_docs)
    
def _gen_config_sidebar(config, dir):
    _gen_sidebar(f"{BASE_DIR}/docs/{dir}", 0)
    
    sidebar = config["themeConfig"]["sidebar"]
    sidebar[f'/{dir}/'] = Path(f"{BASE_DIR}/docs/{dir}/sidebar.js").read_text()


def process_siyuan_export_zip(fp):
    if not os.path.exists(fp):
        raise Exception(f"{fp} not exists.")
    if fp[-4:] != ".zip":
        raise Exception(f"Siyuan export file should be a zip file, but {fp} got.")

    # 创建一个目标文件夹，用于解压缩文件
    target_folder = os.path.join(os.path.dirname(fp), "extracted_contents_23kasdjaklsjdkasd9zxc")
    os.makedirs(target_folder, exist_ok=True)

    # 解压缩文件
    with zipfile.ZipFile(fp, 'r') as zip_ref:
        zip_ref.extractall(target_folder)

    print(f"Successfully extracted contents to: {target_folder}")
    clean_dir(target_folder)

    docs_folder = os.path.join(BASE_DIR, 'docs')
    _, dirs, _ = next(os.walk(target_folder))
    assert len(dirs) == 1
    for folder_name in dirs:
        source_folder = os.path.join(target_folder, folder_name)
        destination_folder = os.path.join(docs_folder, folder_name)

        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)

        shutil.move(source_folder, destination_folder)
        print(f"Moved '{folder_name}' to 'docs' folder.")
        gen_config(folder_name)
    
    shutil.rmtree(target_folder)

def process_docs():
    _, dirs, _ = next(os.walk(f"{BASE_DIR}/docs"))
    for dir in dirs:
        if dir in BLACK_DIR_PATTERN:
            continue
        clean_dir(dir)
        gen_config(dir)

def clean_config():
    full_path = f"{BASE_DIR}/docs/{dir}"
    if not os.path.exists(full_path) or dir in BLACK_DIR_PATTERN:
        return
    config_file = f"{BASE_DIR}/docs/.vuepress/config.js"
    with open(config_file) as f:
        text = f.read()
        text = text.replace("module.exports =","")
    
    config = demjson.decode(text)
    config['themeConfig']['nav'] = []
    config['themeConfig']['sidebar'] = {}

    if SITE_TITLE is not None:
        config["title"] = SITE_TITLE
    
    if SITE_DESC is not None:
        config["description"] = SITE_DESC

    op = "./test_aksdjklamzxncaksldasgd.js"
    demjson.encode_to_file('./test_aksdjklamzxncaksldasgd.js', config, compactly=False, overwrite=True)

    raw_text = Path(op).read_text()
    to_replace = (
        ('"[', '['),
        (']"', ']'),
    )
    for a,b in to_replace:
        raw_text = raw_text.replace(a,b)

    with open(config_file, 'w+') as f:
        f.write(f"module.exports = {raw_text}")
    
    os.remove(op)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Siyuan export and perform various operations.")
    parser.add_argument("command", help="Specify the command to execute (e.g., load).")
    parser.add_argument("-f", "--file", help="File path for Siyuan export zip file.")

    args = parser.parse_args()

    if args.command == "load":
        # example: python process_siyuan_export.py load -f 测试笔记.md.zip
        if args.file:
            process_siyuan_export_zip(args.file)
        else:
            print("Please provide the file path for Siyuan export using -f or --file option.")
    elif args.command == "gen-all":
        # example: python process_siyuan_export.py gen-all
        process_docs()
    elif args.command == "clean-config":
        # example: python process_siyuan_export.py clean-config
        clean_config()
    else:
        print("Invalid command. Please use 'load'.")
