import sys
import os
from os.path import join, getsize
import getopt
import hashlib
import zipfile
import shutil
import json
import time

DEFAULT_TEMP_PATH = "__update_temp"
DEFAULT_CACHE_PATH = "__update_cache"
DEFAULT_RESULT_PATH = "update_gen_result"
LOW_VERSION_TAG = "low"
HIGH_VERSION_TAG = "high"
DIFF_TAG = "diff"
PATCH_SUFFIX = ".zpf"

cur_temp_path = DEFAULT_TEMP_PATH
cur_cache_path = DEFAULT_CACHE_PATH
cur_result_path = DEFAULT_RESULT_PATH

def unzip_file(src, dst):
    zip = zipfile.ZipFile(src, "r")
    zip.extractall(path = dst)
    zip.close()

def zip_file(src, dst):
    f = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)

    for current, subfolder, files in os.walk(src):
        fpath = current.replace(src, "")
        fpath = fpath and fpath + os.sep or ""
        for file in files:
            f.write(join(current, file), fpath + file)
    f.close()

def write_file(content, path):
    file = open(path, 'w')
    file.write(content)
    file.close()

def read_json(file_path):
    content = None
    try:
        with open(file_path, "r", encoding = "utf_8_sig") as load_f:
            content = json.loads(load_f.read())
    except Exception as e:
        log(e)
        on_execute_error("'%s' json parsing failed"%file_path)

    return content

def get_md5(filepath):
    f = open(filepath,'rb')  
    md5obj = hashlib.md5()  
    md5obj.update(f.read())  
    hash = md5obj.hexdigest()  
    f.close()  
    return str(hash).lower()

def get_dir_size(directory):
    size = 0
    for root, dirs, files in os.walk(directory):
        size += sum([getsize(join(root, name)) for name in files])
    return size

def reset_dir(directory, del_self = False):
    if os.path.exists(directory):
        shutil.rmtree(directory, ignore_errors=True)
    if os.path.exists(directory):  # 可能文件占用导致删除失败，多试一次
        shutil.rmtree(directory, ignore_errors=True)
    if os.path.exists(directory):
        on_execute_error("can't delete '%s'"%directory)
    if not del_self:
        os.makedirs(directory)  

def check_file_parent(filepath):
    directory = os.path.split(filepath)[0]
    if directory != "" and not os.path.exists(directory):
        os.makedirs(directory)

def fix_path(path):
    if len(path) == 0: return path
    path = path.replace(r'\/'.replace(os.sep, ''), os.sep)
    if path[-1] == os.sep:
        return path[:-1]
    else:
        return path

def check_path_exist(path):
    if not os.path.exists(path):
        on_execute_error("'%s' does not exist"%path)

def get_asset_path_from_apk(apk_path, tag):
    path = join(cur_temp_path, tag)
    reset_dir(path)
    unzip_file(apk_path, path)
    asset_path = join(path, "assets")
    if not os.path.exists(asset_path):
        on_execute_error("'%s' does not contain asset path"%apk_path)
    return asset_path

def get_asset_path(path, tag):
    check_path_exist(path)
    if os.path.isdir(path):
        # 认为直接是asset路径
        return fix_path(path)
    suffix = os.path.splitext(path)[-1]
    if suffix == ".apk":
        return get_asset_path_from_apk(path, tag)
    else:
        on_execute_error("can't resolve asset path from '%s'"%path)

def copy_diff_file(path, diff_file_path):
    check_file_parent(diff_file_path)
    shutil.copyfile(path, diff_file_path)
    os.utime(diff_file_path, (1636620017, 1636620017))  # 避免访问时间不同，导致相同内容的zip文件md5不同

def generate_diff(low_asset_path, high_asset_path):
    diff_path = join(cur_temp_path, DIFF_TAG)
    reset_dir(diff_path)
    for current, subfolder, files in os.walk(high_asset_path):
        for file in files:
            high_file_path = join(current, file)
            short_path = high_file_path.replace(high_asset_path, "")[1:]
            low_file_path = join(low_asset_path, short_path)
            diff_file_path = join(diff_path, short_path)

            if os.path.exists(low_file_path):
                if getsize(low_file_path) != getsize(high_file_path) or get_md5(low_file_path) != get_md5(high_file_path):
                    # 文件改变
                    copy_diff_file(high_file_path, diff_file_path)
            else:
                # 新增文件
                copy_diff_file(high_file_path, diff_file_path)
    return diff_path

def generate_patch(low_asset_path, high_asset_path, patch_path):
    diff_path = generate_diff(low_asset_path, high_asset_path)
    diff_count = len(os.listdir(diff_path))
    if diff_count == 0:
        return False  # 没有差异
    check_file_parent(patch_path)
    zip_file(diff_path, patch_path)
    return True

def get_version(asset_path):
    file_path = join(asset_path, "ZeusSetting", "BuildinSetting", "HotfixLocalConfig.json")
    check_path_exist(file_path)
    version = read_json(file_path)["ver"]
    if version is None or not version.isdigit():
        on_execute_error("read '%s' version failed, ver is '%s'"%(file_path,version))
    return version


def generate_json(json_file, params):
    content = {
        "Channel": params["channel"],
        "Version": params["version"]
    }
    if "type" in params:
        update_type = params["type"]
        patch_config_data = {
            "Type": update_type,
            "SourceVersion": params["version"],
            "TargetVersion": params["target_version"],
            "OpenTime": params["opentime"],
            "AppStoreUrl": params["app_store_url"],
            "SubChannelAppStoreUrl": params["sub_channel_app_store_url"],
            "PatchMd5": "",
            "PatchPath": "",
            "PatchSize": 0,
            "PatchContentSize": 0,
            "FpPatchMd5": "",
            "FpPatchPath": "",
            "FpPatchSize": 0,
            "FpPatchContentSize": 0
        }
        if "patch_path" in params:
            check_path_exist(params["patch_path"])
            check_path_exist(params["diff_path"])

            patch_md5 = params.get("patch_md5", "")
            if patch_md5 == "":
                patch_md5 = get_md5(params["patch_path"])
            patch_config_data["PatchMd5"] = patch_md5
            patch_config_data["PatchPath"] = "%s/%s/%s%s"%(params["channel"], params["version"], patch_md5, PATCH_SUFFIX)
            patch_config_data["PatchSize"] = getsize(params["patch_path"])
            patch_config_data["PatchContentSize"] = get_dir_size(params["diff_path"])

        if params["test"] is True:
            content["TestingData"] = {}
            if "idfalist" in params and params["idfalist"] != "":
                content["TestingData"]["IDFAList"] = params["idfalist"].split(";")
            content["TestingData"]["PatchConfigData"] = patch_config_data
        else:
            content["PatchConfigData"] = patch_config_data

    json_str = json.dumps(content, indent="    ")
    check_file_parent(json_file)
    write_file(json_str, json_file)

def generate(args):
    channel = args["channel"]
    target_apk_path = args["apk"]

    log("start generate ...")

    check_path_exist(target_apk_path)
    # 读取目标版本
    asset_path = get_asset_path(target_apk_path, "target_apk_unzip")

    target_ver_name = args.get("version", "")
    if target_ver_name == "":
        target_ver_name = get_version(asset_path)

    log("read target version : %s"%target_ver_name)

    if not os.path.exists(cur_cache_path):
        os.mkdir(cur_cache_path)

    cache_channel_path = join(cur_cache_path, channel)
    if not os.path.exists(cache_channel_path):
        log("create channel for caching : %s"%channel)
        os.mkdir(cache_channel_path)
    
    vers = []
    for name in os.listdir(cache_channel_path):
        path = join(cache_channel_path, name)
        if os.path.isdir(path) and name.isdigit():
            ver = int(name)
            target_ver = int(target_ver_name)
            if ver > target_ver:
                on_execute_error("there is a version(%s) larger than the target(%s)"%(ver, target_ver))
            elif ver < target_ver:
                ver_asset_path = join(path, "assets")
                check_path_exist(ver_asset_path)
                vers.append(ver)
    vers.sort()

    cache_target_path = join(cache_channel_path, target_ver_name)
    if os.path.exists(cache_target_path):
        log("warning : '%s' already exists, prepare to delete cache"%target_ver_name)
        reset_dir(cache_target_path, True)

    log("pre-check completed")

    # 准备目标版本
    reset_dir(cur_result_path)
    # 创建频道
    channel_path = join(cur_result_path, channel)
    os.mkdir(channel_path)
    # 创建频道/目标版本
    target_ver_path = join(channel_path, target_ver_name)
    os.mkdir(target_ver_path)
    target_json_file = join(target_ver_path, target_ver_name + ".json")
    generate_json(target_json_file, {"channel" : channel, "version" : target_ver_name})

    log("target version(%s) is generated"%target_ver_name)

    # 处理每个低版本
    for ver in vers:
        ver_name = str(ver)
        ver_path = join(channel_path, ver_name)
        os.mkdir(ver_path)
        temp_patch_path = join(cur_temp_path, "temp.patch")
        ver_json_file = join(ver_path, ver_name + ".json")

        update_type = int(args["type"])
        is_test = False
        if "test" in args:
            if isinstance(args["test"], bool):
                is_test = args["test"]
            elif isinstance(args["test"], str):
                is_test = args["test"] == "true"

        if update_type == 1:  # 商店更新不需要generate_patch
            generate_json(ver_json_file, {
                "channel" : channel,
                "version" : ver_name,
                "type" : update_type,  # 更新类型
                "target_version" : target_ver_name,
                "opentime" : args.get("opentime", ""),
                "app_store_url" : args.get("appstore", ""),
                "sub_channel_app_store_url" : args.get("subappstore", ""),
                "test" : is_test,
                "idfalist" : args.get("idfalist", "")
            })

            log("version(%s) update completed, no need diff : type %s"%(ver_name, update_type))
        else:
            cache_ver_asset_path = join(cache_channel_path, ver_name, "assets")
            has_diff = generate_patch(cache_ver_asset_path, asset_path, temp_patch_path)
            patch_md5 = None
            if has_diff:
                patch_md5 = get_md5(temp_patch_path)
                ver_patch_path = join(ver_path, patch_md5 + PATCH_SUFFIX)
                shutil.move(temp_patch_path, ver_patch_path)
                generate_json(ver_json_file, {
                    "patch_path" : ver_patch_path,
                    "patch_md5" : patch_md5,
                    "diff_path" : join(cur_temp_path, DIFF_TAG),

                    "channel" : channel,
                    "version" : ver_name,
                    "type" : update_type,  # 更新类型
                    "target_version" : target_ver_name,
                    "opentime" : args.get("opentime", ""),
                    "app_store_url" : args.get("appstore", ""),
                    "sub_channel_app_store_url" : args.get("subappstore", ""),
                    "test" : is_test,
                    "idfalist" : args.get("idfalist", "")
                })
            else:
                generate_json(ver_json_file, {
                    "channel" : channel,
                    "version" : ver_name,
                    "test" : is_test,
                    "idfalist" : args.get("idfalist", "")
                })

            log("version(%s) update completed, has diff : %s"%(ver_name, has_diff))

        # 清除老的zpf文件
        # for name in os.listdir(ver_path):
        #     if name.endswith(PATCH_SUFFIX) and (patch_md5 is None or name != (patch_md5 + PATCH_SUFFIX)):
        #         os.remove(join(ver_path, name))  

     # 缓存目标版本
    os.mkdir(cache_target_path)
    shutil.copyfile(target_apk_path, join(cache_target_path, target_ver_name + ".apk"))
    cache_asset_path = join(cache_target_path, "assets")
    shutil.copytree(asset_path, cache_asset_path)

    log("cache version(%s) completed"%target_ver_name)   
            
    log("generate finish.")
                


def usage():
    print("""Usage: python %s -l path -h path -p path [options] 
    -r              : 根目录 (also --root)
    -c              : 频道名称 (also --channel)
    -a              : 目标apk文件路径 (also --apk)
    -t              : 更新类型 (1 : AppStore | 2 : Force | 3 : Recommend | 4 : AppStoreRecommend) (also --type)
Available options are:
    --opentime      : 定期开启时间
    --appstore      : 商店URL
    --subappstore   : 包名对应商店地址
    --temppath      : temp path
    --help          : print this help message and exit"""%sys.argv[0])

def on_arg_error(msg):
    print_error(msg)
    usage()
    sys.exit(2)

def on_execute_error(msg):
    print_error(msg)
    sys.exit(1)

def print_error(msg):
    print("Error: " + msg)

def log(msg):
    print(msg)

def get_params(argv):
    try:
        opts, args = getopt.getopt(argv, "c:a:t:", ["channel=", "apk=", "type=", "opentime=", "appstore=", "subappstore=", "temppath=", "test=", "idfalist=", "version=", "help"])
    except getopt.GetoptError as e:
        on_arg_error(e.msg)
    params = {}
    for opt, arg in opts:
        if opt == "--help":  
            usage() #处理参数 
            sys.exit(2)  
        elif opt in ("-c", "--channel"):
            params["channel"] = arg
        elif opt in ("-a", "--apk"):
            params["apk"] = arg
        elif opt in ("-t", "--type"):
            params["type"] = arg
        elif opt == "--temppath": 
             cur_temp_path = arg
        elif opt[:2] == "--":
            params[opt[2:]] = arg
    return params

def check_params(params):
    if("channel" not in params):
        on_arg_error("lack of channel")
    if("apk" not in params):
        on_arg_error("lack of apk path")
    if "type" not in params: 
        on_arg_error("lack of update type")
    if params["channel"] == "":
        on_arg_error("channel cannot be empty string")
    if not isinstance(params["type"], int) and not params["type"].isdigit():
        on_arg_error("type must be an integer")
    update_type = int(params["type"])
    if not (update_type >= 1 and update_type <= 4):
        on_arg_error("type must be an integer in (1, 2, 3, 4)")
    if "version" in params:
        if not isinstance(params["version"], str) or not params["version"].isdigit():
            on_arg_error("version must be a string type number")

def main(params):
    check_params(params)
    generate(params)

if __name__ == "__main__":
    config_path = "update_config.json"
    if os.path.exists(config_path):  # 读取配置文件
        main(read_json(config_path))
    else:
        main(get_params(sys.argv[1:]))  # 读取命令行参数



