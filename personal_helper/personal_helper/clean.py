import sys, os
from pathlib import Path
import uuid
import shutil
import re

EXCEPTION = ["Audio", "Documents", "Images", "Video", "Archives", "Other"]

CATEGORIES = {
    "Audio": [".mp3", ".aiff", ".oog", ".wav", ".amr"],
    "Documents": [".doc", ".docx", ".txt", ".pdf", ".xlsx", ".pptx"],
    "Images": [".jpeg", ".png", ".jpg", ".svg"],
    "Video": [".avi", ".mp4", ".mov", ".mkv"],
    "Archives": [".zip", ".gz", ".tar"],
    "Other": [],
}
CYRILLIC_SYMBOLS = "абвгґдеёєжзиіїйклмнопрстуфхцчшщъыьэюя"
TRANSLATION = (
    "a",
    "b",
    "v",
    "h",
    "g",
    "d",
    "e",
    "e",
    "ie" "zh",
    "z",
    "y",
    "i",
    "yi",
    "y",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "r",
    "s",
    "t",
    "u",
    "f",
    "kh",
    "ts",
    "ch",
    "sh",
    "shch",
    "",
    "y",
    "",
    "e",
    "yu",
    "ya",
)

BAD_SYMBOLS = ("%", "*", " ", "-")

TRANS = {}

dict_search_result = {}


def unpack_archive(item: Path, cat: Path):
    archive_name = item.stem
    output_dir = cat / archive_name
    output_dir.mkdir(exist_ok=True)

    shutil.unpack_archive(str(item), str(output_dir))


def delete_empty_folders(path):
    path = Path(path)
    if not path.is_dir():
        return

    for item in path.iterdir():
        if item.is_dir():
            delete_empty_folders(item)
    if not any(True for _ in path.iterdir()):
        path.rmdir()


def delete_arch_files(path):
    path = Path(path)

    if path.is_dir():
        for item in path.iterdir():
            delete_arch_files(item)

    if path.is_file() and path.suffix.lower() in (".zip", ".tar", ".gz"):
        path.unlink()


def file_list():
    lst = []
    longest_element = ""
    for category, value in dict_search_result.items():
        for element in value[0]:
            if len(element) > len(longest_element):
                longest_element = element
              
        ext = "Extensions: " + ", ".join(value[1]) 
        if len(ext) > len(longest_element):
            longest_element = ext

    oll_length = len(longest_element) + 2

    lst.append("|" + "=" * oll_length + "|")
    for category, value in dict_search_result.items():
        lst.append("|{:^{length}}|".format(str(category), length=oll_length))
        lst.append("|" + "=" * oll_length + "|")
        ext = "Extensions: "
        for extension in value[1]:
            ext += re.sub("\.", "", extension) + ", "
        ext = ext[:-2]
        lst.append("|{:<{length}}|".format(ext, length=oll_length))
        lst.append("|" + "-" * oll_length + "|")
        for element in value[0]:
            lst.append("|{:<{length}}|".format(element, length=oll_length))
        lst.append("|" + "=" * oll_length + "|")
    for i in lst:
        print(i)

    return lst


def normalize(name: str) -> str:
    for c, t in zip(list(CYRILLIC_SYMBOLS), TRANSLATION):
        TRANS[ord(c)] = t
        TRANS[ord(c.upper())] = t.upper()

    for i in BAD_SYMBOLS:
        TRANS[ord(i)] = "_"

        trans_name = name.translate(TRANS)
    return trans_name


def move_file(file: Path, root_dir: Path, categorie: str) -> None:
    ext = set()
    global dict_search_result
    target_dir = root_dir.joinpath(categorie)
    if not target_dir.exists():
        # print(f"Creation {target_dir}") # друкує теку яку сортуємо
        target_dir.mkdir()

    if file.suffix.lower() in (".zip", ".tar", ".gz"):
        try:
            unpack_archive(file, target_dir)
        except shutil.ReadError:
            return

    new_name = target_dir.joinpath(f"{normalize(file.stem)}{file.suffix}")
    if new_name.exists():
        new_name = new_name.with_name(f"{new_name.stem}-{uuid.uuid4()}{file.suffix}")
    file.rename(new_name)
    ext.add(file.suffix)

    if categorie in dict_search_result:
        dict_search_result[categorie][0].append(new_name.name)
        dict_search_result[categorie][1].update(ext)
    else:
        dict_search_result[categorie] = [[new_name.name], ext]


def get_categories(file: Path) -> str:
    ext = file.suffix.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "Other"


def sort_folder(path: Path) -> None:
    for item in path.glob("**/*"):
        # print(item)
        if item.is_dir() and item.name in EXCEPTION:
            return
        if item.is_file():
            cat = get_categories(item)
            move_file(item, path, cat)


def save_log(list):
    absolute_path = os.path.abspath(sys.argv[0])
    path = Path(sys.path[0]).joinpath("Sort_Log.txt")
    with open(path, "w") as file:
        file.writelines(str(item) + "\n" for item in list)


# =========================================
def sort_main(argv):
    try:
        path = Path(argv)
    except IndexError:
        return "No folder specified for sorting"

    if not path.exists():
        return f"This {path} does not exist."

    sort_folder(path)
    delete_empty_folders(path)
    delete_arch_files(path)
    # file_list()
    save_log(file_list())
    return f"The folder {path} is sorted - [bold green]success[/bold green]"


if __name__ == "__main__":
    print(sort_main())
