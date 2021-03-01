from xml.etree import ElementTree as ET


# import codecs
# import os
# import refine


def collect_text_from_p(p_element):
    text = "".join(p_element.itertext())
    if '\n' in text:
        text = text.replace('\n', '')
    return text


def handle_list_points(list_element, prefix):
    points_list = " "
    intro = list_element.find(prefix + 'intro')
    if intro is not None:
        points_list += collect_text_from_p(list_element.find(prefix + 'intro').find(prefix + 'p')) + "\n"
    for sub_point in list_element.findall(prefix + "point"):
        sub_list = sub_point.find(prefix + 'list')
        if sub_list is not None:
            point_num = "" if sub_point.find(prefix + "num") is None else sub_point.find(prefix + "num").text
            points_list += point_num + handle_list_points(sub_list, prefix)

        else:
            point_num = "" if sub_point.find(prefix + "num") is None else sub_point.find(prefix + "num").text
            points_list += point_num + collect_text_from_p(sub_point.find(prefix + 'content').find(prefix + 'p')) + "\n"
    return points_list


def handle_point(point_element, prefix):  # this function handles one specific side point
    authorial_note = point_element.find('.//' + prefix + 'authorialNote')
    if authorial_note is not None and authorial_note.attrib.get('placement') == 'side':
        # this is side title.
        headline = authorial_note[0].text  # headline of the sub-paragraph
        if headline == " " or headline == "" or headline == "/n":
            return
        sub_list = point_element.find(prefix + 'list')
        point_dict = {"point headline": headline,
                          "point number": point_element.find(prefix + 'num').text}
        if sub_list is not None:  # in case we have sub point within a list, go over all points
                point_dict["content"] = handle_list_points(sub_list, prefix)
        else:  # in case we dont have sub points
                point_dict["content"] = collect_text_from_p(point_element.find(prefix + 'content').find(prefix + 'p'))
        return point_dict


def collect_law_data(filename):
    law_data = {}
    law_tree = ET.parse(filename)
    law_root = law_tree.getroot()
    prefix = '{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}'
    law_data["law_name"] = law_root.find('.//' + prefix + 'body')[0][0][0].text
    date = law_root.find('.//' + prefix + 'FRBRdate').attrib.get("date")
    if date == "UnknownWorkDate":
        law_data["date"] = "0"
    else:
        law_data["date"] = date
    law_data["points"] = []
    for list_element in law_root.find('.//' + prefix + 'body').findall('.//' + prefix + 'list'):
        if list_element is None:
            break
        point_element = list_element.find(prefix + 'point')
        if point_element and point_element.find('.//' + prefix + 'authorialNote'):
            for point in list_element.findall(prefix + 'point'):
                p_list = handle_point(point, prefix)
                if p_list is not None:
                    law_data["points"].append(p_list)
    return law_data
