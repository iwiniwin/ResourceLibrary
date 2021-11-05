import sys
import os
from os.path import join, getsize
import getopt
import hashlib
import zipfile
import shutil
import json

DEFAULT_TEMP_PATH = "__update_temp"
LOW_VERSION_TAG = "low"
HIGH_VERSION_TAG = "high"
DIFF_TAG = "diff"
cur_temp_path = DEFAULT_TEMP_PATH

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

def reset_dir(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)  

def check_file_parent(filepath):
    directory = os.path.split(filepath)[0]
    if directory != "" and not os.path.exists(directory):
        os.makedirs(directory)

def get_asset_path_from_apk(apk_path, tag):
    path = join(cur_temp_path, tag)
    reset_dir(path)
    unzip_file(apk_path, path)
    asset_path = join(path, "assets")
    if not os.path.exists(asset_path):
        on_execute_error("'%s' does not contain asset path"%apk_path)
    return asset_path

def get_asset_path(path, tag):
    if not os.path.exists(path):
        on_execute_error("'%s' does not exist"%path)
    if os.path.isdir(path):
        # 认为直接是asset路径
        if path[-1] == "/" or path[-1] == "\\":
            return path[:-1]
        else:
            return path
    suffix = os.path.splitext(path)[-1]
    if suffix == ".apk":
        return get_asset_path_from_apk(path, tag)
    else:
        on_execute_error("can't resolve asset path from '%s'"%path)

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
                md5 = get_md5(high_file_path)
                if get_md5(low_file_path) != md5:
                    # 文件改变
                    check_file_parent(diff_file_path)
                    shutil.copyfile(high_file_path, diff_file_path)
            else:
                # 新增文件
                check_file_parent(diff_file_path)
                shutil.copyfile(high_file_path, diff_file_path)
    return diff_path

def generate_patch(low_version_path, high_version_path, patch_path):
    low_asset_path = get_asset_path(low_version_path, LOW_VERSION_TAG)
    high_asset_path = get_asset_path(high_version_path, HIGH_VERSION_TAG)
    diff_path = generate_diff(low_asset_path, high_asset_path)
    check_file_parent(patch_path)
    zip_file(diff_path, patch_path)

def generate_json(params):
    patch_path = params["patch"]
    diff_path = join(cur_temp_path, DIFF_TAG)

    if not os.path.exists(patch_path):
        on_execute_error("'%s' does not exist"%patch_path)
    if not os.path.exists(diff_path):
        on_execute_error("'%s' does not exist"%diff_path)

    json_file = params["jsonfile"]
    content = {
        "Channel" : params["channel"],
        "Version": "278",
        "PatchConfigData" : {
            "Type": int(params["type"]),
            "SourceVersion": "278",
            "TargetVersion": "283",
            "OpenTime": params.get("opentime", ""),
            "AppStoreUrl": "https://play.google.com/store/apps/details?id=com.ryipgx.tom",
            "SubChannelAppStoreUrl": "",
            "PatchMd5": get_md5(patch_path),
            "PatchPath": "Android_publish/278/98181dba8f29d5ded9f2ad8e48026b76.zpf",
            "PatchSize": getsize(patch_path),
            "PatchContentSize": get_dir_size(diff_path),
            "FpPatchMd5": "",
            "FpPatchPath": "",
            "FpPatchSize": 0,
            "FpPatchContentSize": 0
        },
    }
    json_str = json.dumps(content, indent="    ")
    check_file_parent(json_file)
    write_file(json_str, json_file)

def usage():
    print("""Usage: python %s -l path -h path -p path [options] 
    -l path     : low version path (also --low)
    -h path     : high version path (also --high)
    -p path     : patch file path (also --patch)
Available options are:
    --temppath  : temp path
    -help       : print this help message and exit"""%sys.argv[0])

def on_arg_error(msg):
    print_error(msg)
    usage()
    sys.exit(2)

def on_execute_error(msg):
    print_error(msg)
    sys.exit(1)

def print_error(msg):
    print("Error: " + msg)

def get_params(argv):
    try:
        opts, args = getopt.getopt(argv, "l:h:p:", ["low=", "high=", "patch=", "temppath=", "jsonfile=", "channel=", "type=", "opentime=", "help"])
    except getopt.GetoptError as e:
        on_arg_error(e.msg)
    params = {}
    for opt, arg in opts:
        if opt == "--help":  
            usage() #处理参数 
            sys.exit(2)  
        elif opt in ("-l", "--low"):
            params["low"] = arg
        elif opt in ("-h", "--high"):
            params["high"] = arg
        elif opt in ("-p", "--patch"):
            params["patch"] = arg
        elif opt == "--temppath": 
             cur_temp_path = arg
        elif opt[:2] == "--":
            params[opt[2:]] = arg
    return params

def main(argv):
    params = get_params(argv)
    
    if("low" not in params):
        on_arg_error("lack of low version path")
    if("high" not in params):
        on_arg_error("lack of high version path")
    if("patch" not in params):
        on_arg_error("lack of patch file path")

    generate_patch(params["low"], params["high"], params["patch"])

    if "jsonfile" in params:
        if "channel" not in params:
            on_arg_error("lack of channel when generating json")
        if "type" not in params:
            on_arg_error("lack of type when generating json")
        if not params["type"].isdigit():
            on_arg_error("type must be an integer")
        generate_json(params)

if __name__ == "__main__":
    main(sys.argv[1:])    



