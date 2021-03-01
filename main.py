import os
from flask import Flask, render_template, redirect, request, url_for, session
# from flask_table import Item, ItemTable
from law_manager import collect_law_data
import json
from functools import cmp_to_key
import distance
from YAP_Wrapper.yap_api import YapApi
import subprocess
import zlib, base64
import compress_json

app = Flask(__name__)
app.secret_key = "efrat and yuval"

data = []
result = []
count = 1
ip = '127.0.0.1:8000'
yap = YapApi()


def collect_yap_data():
    global ip
    global yap
    for law in data:
        for point in law["points"]:
            if point:
                point_headline = point["point headline"]
                tokenized_text, segmented_text, lemmas, dep_tree, md_lattice, ma_lattice = yap.run(point_headline, ip)
                new_segmented = clean_prefix(segmented_text)
                new_lemmas = clean_prefix(lemmas)
                point["yap"] = [tokenized_text, new_segmented, new_lemmas]


def clean_prefix(yap_text):
    new_text = yap_text.split(' ')
    for i in range(len(new_text)):
        if len(new_text[i]) == 1:
            new_text[i] = ''
    new_text = " ".join(new_text).replace("  ", ' ')  # with no prefix char
    return new_text


def clean(list):
    if '' in list:
        list.remove('')


def similar(point, search_word, search_segmented, search_lemmas):
    headline = point["point headline"]
    point_segmented_text = point["yap"][1]
    point_lemmas = point["yap"][2]
    #is_search_in_headline = True
    #is_lemma_word_in_headline = True
    #is_segment_word_in_headline = True

    split_search = search_word.split(" ")
    split_search_segment = search_segmented.split(" ")
    split_search_lemmas = search_lemmas.split(" ")

    split_lemmas_point = point_lemmas.split(" ")
    split_headline = headline.split(" ")
    split_segment_point = point_segmented_text.split(" ")

    split_headline += split_segment_point + split_lemmas_point
    clean(split_search)
    clean(split_search_segment)
    clean(split_search_lemmas)

    for i in range(len(split_search)):
        if split_search[i] not in split_headline:
            if split_search_segment[i] not in split_headline:
                if split_search_lemmas[i] not in split_headline:
                    return False

    # for word in split_search:
    #     if word not in split_headline:
    #         is_search_in_headline = False
    #
    # for word in split_search_segment:
    #     if word not in split_segment_point:
    #         is_segment_word_in_headline = False
    #
    # for word in split_search_lemmas:
    #     if word not in split_lemmas_point:
    #         is_lemma_word_in_headline = False
    #
    # if not is_lemma_word_in_headline and not is_segment_word_in_headline and not is_search_in_headline:
    #     return False
    return True


def search(search_word):
    global ip
    global yap
    global data
    points_list = []
    index = 1
    tokenized_text, segmented_text, lemmas, dep_tree, md_lattice, ma_lattice = yap.run(search_word, ip)
    search_segmented = clean_prefix(segmented_text)
    search_lemmas = clean_prefix(lemmas)
    print(search_segmented)
    print(search_lemmas)
    for law in data:
        if law and law["points"]:
            for point in law["points"]:
                if point:
                    is_short_content = True
                    if similar(point, search_word, search_segmented, search_lemmas):
                        content = point["content"].split("\n")
                        clean(content)
                        if len(content) > 3:
                            is_short_content = False
                        points_list.append({"law name": law["law_name"],
                                            "date": law["date"],
                                            "point headline": point["point headline"],
                                            "content": content,
                                            "index": str(index),
                                            "short": is_short_content})
                        index += 1

    return points_list


def open_files_and_collect_data():
    path = "".join(os.getcwd())
    for root, subFolder, files in os.walk(path):
        for item in files:
            if item.endswith("main.xml"):
                file_name_path = str(root) + "\main.xml"
                law_data = collect_law_data(file_name_path)
                if law_data is not None:
                    data.append(law_data)


def compare(item1, item2):
    if item1["date"] == '0' or item2["date"] == '0':
        return -1
    date1 = item1["date"]
    date2 = item2["date"]
    split_date1 = date1.split("-")
    split_date2 = date2.split("-")
    if split_date1[0] == split_date2[0]:
        if split_date1[1] == split_date2[1]:
            if split_date1[2] == split_date2[2]:
                return 0
            else:
                return int(split_date1[2]) - int(split_date2[2])
        else:
            return int(split_date1[1]) - int(split_date2[1])
    else:
        return int(split_date1[0]) - int(split_date2[0])


def sort_by_date(results):
    return sorted(results, reverse=True, key=cmp_to_key(compare))


@app.route("/result", methods=['GET', 'POST'])
def result_found():
    global count
    global result
    res_len = len(result)
    if request.method == 'POST':
        if request.form["submit_button"] == "new search":
            return redirect(url_for("home"))
        elif request.form["submit_button"] == "load more":
            count += 1
        elif request.form["submit_button"] == "sort":
            result = sort_by_date(result)
    # for point in result:
    #     print(point["index"])
    return render_template("result.html", results=result[:count * 20], count=count * 20, result_len=res_len)


@app.route('/', methods=['GET', 'POST'])
def home():
    global result
    global count
    if request.method == 'POST':
        search_word = request.form["search bar"]
        result = search(search_word)
        count = 1
        return redirect(url_for("result_found"))
    else:
        return render_template("search.html")


if __name__ == '__main__':
    if not (os.path.isfile('comp_data.json.gz') and os.access('comp_data.json.gz', os.R_OK)):
        if not (os.path.isfile('data.txt') and os.access('data.txt', os.R_OK)):
            with open("data.txt", "w", encoding='utf8') as jsonfile:
                open_files_and_collect_data()
                collect_yap_data()
                json.dump(data, jsonfile, ensure_ascii=False)

        with open('data.txt', encoding='utf8') as data_json:
            data_load = json.load(data_json)
            compress_json.dump(data_load, "comp_data.json.gz")

    data = compress_json.load("comp_data.json.gz")
    app.run()
