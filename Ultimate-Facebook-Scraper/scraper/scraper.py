# -*- coding: utf-8 -*-
import ast
import json
import os
import sys
import urllib
import traceback

from datetime import datetime

import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter

import yaml
import utils
import argparse
import pymongo
import random
import base64
import requests
import schedule
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from flask import Flask, request, Response, render_template
from flask_cors import CORS, cross_origin

logger = logging.getLogger('RotatingFileHandler')
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler('logs/log_filename.log', maxBytes=10000000, backupCount=100)
formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
mydb = myclient["data_crawlFB"]

with open("../credentials.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(stream=ymlfile)

def get_as_base64(url):
    return base64.b64encode(requests.get(url).content)
def get_facebook_images_url(img_links):
    urls = []

    for link in img_links:
        if link != "None":
            valid_url_found = False
            driver.get(link)
            sleep(random.randint(3,5))

            try:
                while not valid_url_found:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located(
                            (By.ID, "mount_0_0")
                        )
                    )

                    element = driver.find_element_by_class_name(
                        selectors.get("spotlight")
                    )
                    img_url = element.get_attribute("src")

                    if img_url.find(".jpg") != -1 or img_url.find(".png") != -1:
                        valid_url_found = True
                        urls.append(img_url)
            except Exception:
                urls.append("None")
        else:
            urls.append("None")

    return urls

def get_facebook_images_post_url(post_id_link):
    url = []

    if post_id_link != -1:
        valid_url_found = False
        driver.get(post_id_link)
        sleep(2)

        try:
            # while not valid_url_found:
            #     WebDriverWait(driver, 30).until(
            #         EC.presence_of_element_located(
            #             (By.ID, "mount_0_0")
            #         )
            #     )
            #     elements = driver.find_elements_by_css_selector(".i09qtzwb.n7fi1qx3.datstx6m.pmk7jnqg.j9ispegn.kr520xx4.k4urcfbm")
            #     for element in elements:
            #         img_post = element.get_attribute("src")
            #         url.append(img_post)
            #     if img_post.find(".jpg") != -1 or img_post.find(".png") != -1:
            #         valid_url_found = True
            #         url.append(img_post)
            elements = driver.find_elements_by_css_selector(
                ".i09qtzwb.n7fi1qx3.datstx6m.pmk7jnqg.j9ispegn.kr520xx4.k4urcfbm")
            if(elements != []):
                for element in elements:
                    img_post = element.get_attribute("src")
                    url.append(img_post)
                if img_post.find(".jpg") != -1 or img_post.find(".png") != -1:
                    valid_url_found = True
                    url.append(img_post)
        except Exception :
            url = []
    else:
        url = []

    return url
# -------------------------------------------------------------
# -------------------------------------------------------------

# takes a url and downloads image from that url
def image_downloader(img_links, folder_name,collection_name,status):
    """
    Download images from a list of image urls.
    :param img_links:
    :param folder_name:
    :return: list of image names downloaded
    """
    img_names = []
    try:
        if status == 1:
            path = cfg["path"]
            parent = path + "/data/" + collection_name + "/Photos"
        else:
            path = cfg["pathgroup"]
            item = "GroupPhotos"
            parent = path + "/data/" + collection_name + "/" + item
        try:
            folder = os.path.join(parent, folder_name)
            utils.create_folder(folder)
            # os.chdir(folder)
        except Exception:
            print("Error in changing directory.")

        for link in img_links:
            img_name = "None"

            if link != "None":
                img_name = (link.split(".jpg")[0]).split("/")[-1] + ".jpg"
                path_img = folder+"/"+img_name
                # this is the image id when there's no profile pic
                if img_name == selectors.get("default_image"):
                    img_name = "None"
                else:
                    try:
                        urllib.request.urlretrieve(link, path_img)
                    except Exception:
                        img_name = "None"
            img_names.append(img_name)
        # os.chdir(parent)
    except Exception:
        print("Exception (image_downloader):", sys.exc_info()[0])
    return img_names

def image_posts_downloader(img_links, folder_name, user_name, item):
    """
    Download images from a list of image urls.
    :param img_links:
    :param folder_name:
    :return: list of image names downloaded
    """
    img_names = []

    try:
        for link in img_links:
            img_name = "None"

            if link != "None":
                img_name = (link.split(".jpg")[0]).split("/")[-1] + ".jpg"
                path = cfg["path"]
                parent = path + "/data/" + user_name + "/" + item
                try:
                    folder = os.path.join(parent, folder_name)
                    utils.create_folder(folder)
                    # os.chdir(folder)
                except Exception:
                    print("Error in changing directory.")
                path_img = folder + "/" + img_name
                # this is the image id when there's no profile pic
                if img_name == selectors.get("default_image"):
                    img_name = "None"
                else:
                    try:
                        urllib.request.urlretrieve(link, path_img)
                    except Exception:
                        img_name = "None"
                        os.rmdir(os.path.join(folder))

            img_names.append(img_name)

        # os.chdir(parent)
    except Exception:
        print("Exception (image_downloader):", sys.exc_info()[0])
    return img_names
# -------------------------------------------------------------
# -------------------------------------------------------------


def extract_and_write_posts(elements, filename, user_name, item):
    try:
        list_post = []
        ids = []
        for x in elements:
            try:
                if x.find(".php") != -1:
                    post_id_link = (
                            facebook_https_prefix + facebook_link_body + (x.split("=")[2].split("&")[0]) + "/posts/" + (x.split("=")[1].split("&")[0])
                    )
                else:
                    post_id_link = x.split("?")[0]
                ids.append(post_id_link)
            except Exception:
                pass
        for id in ids:
            if id != -1:
                post_id = id.split("/")[-1]
                try:
                    background_post_links = get_facebook_images_post_url(id)
                    folder_names = post_id
                    print("Downloading " + folder_names)
                    if background_post_links != []:
                        img_names = image_posts_downloader(
                            background_post_links, folder_names, user_name, item
                        )
                        img_names.append(img_names)

                    _data_post = get_comments_post_profile(filename, user_name, item, folder_names )
                    list_post.append(_data_post)
                    sleep(random.randint(2,5))
                except Exception as ex:
                    # Get current system exception
                    ex_type, ex_value, ex_traceback = sys.exc_info()

                    # Extract unformatter stack traces as tuples
                    trace_back = traceback.extract_tb(ex_traceback)

                    # Format stacktrace
                    stack_trace = list()

                    for trace in trace_back:
                        stack_trace.append(
                            "File : %s , Line : %d, Func.Name : %s, Message : %s" % (
                            trace[0], trace[1], trace[2], trace[3]))
                    logging.error("this is error" + str(stack_trace))
                    pass
    except ValueError:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    except Exception:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    return list_post
def get_comments_post_profile(file_name, user_name, item, folder_names):
    path = cfg["path"]
    fz = path + "/data/" + user_name + "/" + item + "/" + folder_names + "/" + file_name
    patd_img_post = path + "/data/" + user_name + "/" + item + "/" + folder_names + "/"

    showmore_elements = driver.find_elements_by_css_selector(".rq0escxv.l9j0dhe7.du4w35lb.q9uorilb.cbu4d94t.g5gj957u.d2edcug0.hpfvmrgz.rj1gh0hx.buofh1pr.n8tt0mok.hyh9befq.r8blr3vg.jwdofwj8.g0qnabr5.ni8dbmo4.stjgntxs.ltmttdrg")
    for showmore_element in showmore_elements:
        showmore_element.click()
        sleep(random.randint(2, 5))

    list_cmt_parent = driver.find_elements_by_css_selector(".l9j0dhe7.ecm0bbzt.rz4wbd8a.qt6c0cv9.dati1w0a.j83agx80.btwxx1t3.lzcic4wl")
    jsonData = {}
    post_id = folder_names
    post_id_key = "post_id"
    jsonData[post_id_key] = post_id
    #lay time bai post
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time_key = "time"
    jsonData[time_key] = time
    post_status_element = driver.find_elements_by_css_selector(".kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql")
    status_value = ""
    if len(post_status_element) > 0:
        status_value = post_status_element[0].get_attribute('innerText')
    status_key = "Status"
    jsonData[status_key] = status_value

    img_key = "Photos_Status"
    string_va = []
    try:
        for path in os.listdir(patd_img_post):
            if(path.find("json") == -1):
                full_path = os.path.join(patd_img_post, path)
                if os.path.isfile(full_path):
                    string_va.append({
                        'name': path,
                        'link': full_path
                    })
        jsonData[img_key] = string_va
    except:
        # cmt_parent_element = list_cmt_parent[0].find_elements_by_css_selector(".kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql")
        # if post_status_element[1] != cmt_parent_element[0]:
        #     status_value = post_status_element[1].get_attribute('innerText')
        #     status_key = "Status"
        #     jsonData[status_key] = status_value
        print("Khong co anh trong status")
    for cmt_parent in list_cmt_parent:
        cmt_parent_key = "Bình luận"
        comments_post_element = cmt_parent.find_element_by_xpath('../..')
        cmt_parent_element = cmt_parent.find_elements_by_css_selector(".kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql")
        cmt_parent_text = "Ảnh"
        if len(cmt_parent_element)>0:
            cmt_parent_text = cmt_parent_element[0].get_attribute('innerText')
        cmt_parent_name_element = cmt_parent.find_element_by_css_selector(".oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.gmql0nx0.gpro0wi8")
        cmt_parent_name = cmt_parent_name_element.get_attribute('innerText')
        cmt_parent_link_element = cmt_parent.find_element_by_css_selector(".oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.gmql0nx0.gpro0wi8")
        cmt_parent_link = cmt_parent_link_element.get_attribute("href")
        if cmt_parent_link.find(".php") != -1:
            cmt_parent_link = (
                    facebook_https_prefix + facebook_link_body +  (cmt_parent_link.split("=")[1].split("&")[0])
            )
        else:
            cmt_parent_link = cmt_parent_link.split("?")[0]
        list_cmt_child = comments_post_element.find_elements_by_css_selector(".l9j0dhe7.ecm0bbzt.rz4wbd8a.qt6c0cv9.scb9dxdr.j83agx80.btwxx1t3.lzcic4wl")
        cmt_child_values = []
        for cmt_child in list_cmt_child:
            try:
                cmt_child_text = "ảnh"
                cmt_child_value_element = cmt_child.find_elements_by_css_selector(".kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql")
                if len(cmt_child_value_element)>0:
                    cmt_child_text = cmt_child_value_element[0].get_attribute('innerText')
                cmt_child_name_element = cmt_child.find_element_by_css_selector(".d2edcug0.hpfvmrgz.qv66sw1b.c1et5uql.lr9zc1uh.a8c37x1j.keod5gw0.nxhoafnm.aigsh9s9.d9wwppkn.fe6kdd0r.mau55g9w.c8b282yb.mdeji52x.e9vueds3.j5wam9gi.lrazzd5p.oo9gr5id")
                cmt_child_name = cmt_child_name_element.get_attribute('innerText')
                cmt_child_link_element = cmt_child.find_element_by_css_selector(".tw6a2znq.sj5x9vvc.d1544ag0.cxgpxx05")
                cmt_child_link = cmt_child_link_element.find_element_by_tag_name('a').get_attribute("href")
                if(cmt_child_link.find(".php") != -1):
                    cmt_child_link = cmt_child_link.split("&")[0]
                else:
                    cmt_child_link = cmt_child_link.split("?")[0]
                cmt_child_values.append({
                    'name': cmt_child_name,
                    'link': cmt_child_link,
                    "comment": cmt_child_text
                })
            except Exception as ex:
                # Get current system exception
                ex_type, ex_value, ex_traceback = sys.exc_info()

                # Extract unformatter stack traces as tuples
                trace_back = traceback.extract_tb(ex_traceback)

                # Format stacktrace
                stack_trace = list()

                for trace in trace_back:
                    stack_trace.append(
                        "File : %s , Line : %d, Func.Name : %s, Message : %s" % (
                            trace[0], trace[1], trace[2], trace[3]))
                logging.error("this is error" + str(stack_trace))
        if cmt_parent_key in jsonData:
            cmt_parent_values = jsonData[cmt_parent_key]
        else:
            cmt_parent_values = []
        cmt_parent_values.append({
            'name': cmt_parent_name,
            'link': cmt_parent_link,
            "comment": cmt_parent_text,
            "Trả lời": cmt_child_values
        })
        jsonData[cmt_parent_key] = cmt_parent_values
    return jsonData

def get_status_and_title(link, x):
    post_status_element = x.find_elements_by_css_selector(".kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql.ii04i59q")
    status = ""
    if len(post_status_element) > 0:
        status = post_status_element[0].get_attribute('innerText')
    link_element = x.find_elements_by_css_selector(".oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.m9osqain.gpro0wi8.knj5qynh")
    if len(link_element) > 0:
        link = link_element[0].get_attribute("href")
    print(link)
    return status, link


def extract_and_write_group_posts(elements, filename):
    try:
        f = create_post_file(filename)
        ids = []
        for x in elements:
            try:
                # id
                post_id = utils.get_group_post_id(x)
                ids.append(post_id)
            except Exception:
                pass
        total = len(ids)
        i = 0
        for post_id in ids:
            i += 1
            try:
                add_group_post_to_file(f, filename, post_id, i, total, reload=True)
            except ValueError:
                pass
        f.close()
    except ValueError:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    except Exception:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    return


def add_group_post_to_file(f, filename, post_id, number=1, total=1, reload=False):
    print("Scraping Post(" + post_id + "). " + str(number) + " of " + str(total))
    photos_dir = os.path.dirname(filename)
    if reload:
        driver.get(utils.create_post_link(post_id, selectors))
    line = get_group_post_as_line(post_id, photos_dir)
    try:
        f.writelines(line)
    except Exception:
        print("Posts: Could not map encoded characters")


def create_post_file(filename):
    """
    Creates post file and header
    :param filename:
    :return: file
    """
    f = open(filename, "w", newline="\r\n", encoding="utf-8")
    f.writelines(
        "TIME || TYPE  || TITLE || STATUS || LINKS(Shared Posts/Shared Links etc) || POST_ID || "
        "PHOTO || COMMENTS " + "\n"
    )
    return f


# -------------------------------------------------------------
# -------------------------------------------------------------


def save_to_file(name, elements, status, current_section,collection_name):
    """helper function used to save links to files"""
    # status 0 = dealing with friends list
    # status 1 = dealing with photos
    # status 2 = dealing with videos
    # status 3 = dealing with about section
    # status 4 = dealing with posts
    # status 5 = dealing with group posts
    try:
        if status != 5:
            path = cfg["path"]
            fz = path + "/data/" + collection_name + "/Photos/" + name
        else:
            path = cfg["pathgroup"]
            fz = path + "/data/" + collection_name + "/GroupPhotos/" + name
        # f = None  # file pointer

        if status != 4:
            f = open(name, "w", encoding="utf-8", newline="\r\n")
        # driver.get(page)
        # WebDriverWait(driver, 30).until(
        #     EC.presence_of_element_located(
        #         (By.ID, "mount_0_0")
        #     )
        # )
        results = []
        img_names = []

        # dealing with Friends
        if status == 0:
            # get profile links of
            if current_section == 0:
                friends_links = elements.find_elements_by_css_selector(".buofh1pr.hv4rvrfc")
                jsonData = {}
                for friends_link in friends_links:
                    friends_name_key = "All_friend"
                    friends_name = friends_link.find_element_by_css_selector(".oo9gr5id")
                    friend_name = friends_name.text
                    friend_link = friends_link.find_element_by_css_selector(".oajrlxb2")
                    link = friend_link.get_attribute("href")
                    link = create_original_link(link)
                    if (link[-1] == '/'):
                        link = link[:-1]
                    if friends_name_key in jsonData:
                        friend_values = jsonData[friends_name_key]
                    else:
                        friend_values = []
                    friend_values.append({
                        'name': friend_name,
                        'link': link
                    })
                    jsonData[friends_name_key] = friend_values
                # json.dump(jsonData, f, ensure_ascii=False)
                # collection_currency = mydb['friends']
                # collection_currency.insert_one(jsonData)
                #myclient.close()
                return jsonData
            if current_section == 1:
                friends_links = elements.find_elements_by_css_selector(".buofh1pr.hv4rvrfc")
                jsonData = {}
                for friends_link in friends_links:
                    friends_name_key = "following"
                    friends_name = friends_link.find_element_by_css_selector(".oo9gr5id")
                    friend_name = friends_name.text
                    friend_link = friends_link.find_element_by_css_selector(".oajrlxb2")
                    link = friend_link.get_attribute("href")
                    link = create_original_link(link)
                    if (link[-1] == '/'):
                        link = link[:-1]
                    if friends_name_key in jsonData:
                        friend_values = jsonData[friends_name_key]
                    else:
                        friend_values = []
                    friend_values.append({
                        'name': friend_name,
                        'link': link
                    })
                    jsonData[friends_name_key] = friend_values
                # json.dump(jsonData, f, ensure_ascii=False)
                # collection_currency = mydb['friends']
                # collection_currency.insert_one(jsonData)
                return jsonData
            if current_section == 2:
                friends_links = elements.find_elements_by_css_selector(".buofh1pr.hv4rvrfc")
                jsonData = {}
                for friends_link in friends_links:
                    friends_name_key = "followers"
                    friends_name = friends_link.find_element_by_css_selector(".oo9gr5id")
                    friend_name = friends_name.text
                    friend_link = friends_link.find_element_by_css_selector(".oajrlxb2")
                    link = friend_link.get_attribute("href")
                    link = create_original_link(link)
                    if (link[-1] == '/'):
                        link = link[:-1]
                    if friends_name_key in jsonData:
                        friend_values = jsonData[friends_name_key]
                    else:
                        friend_values = []
                    friend_values.append({
                        'name': friend_name,
                        'link': link
                    })
                    jsonData[friends_name_key] = friend_values
                # json.dump(jsonData, f, ensure_ascii=False)
                # collection_currency = mydb['friends']
                # collection_currency.insert_one(jsonData)
                return jsonData
            if current_section == 3:
                friends_links = elements.find_elements_by_css_selector(".buofh1pr.hv4rvrfc")
                jsonData = {}
                for friends_link in friends_links:
                    friends_name_key = "friends_college"
                    friends_name = friends_link.find_element_by_css_selector(".oo9gr5id")
                    friend_name = friends_name.text
                    friend_link = friends_link.find_element_by_css_selector(".oajrlxb2")
                    link = friend_link.get_attribute("href")
                    link = create_original_link(link)
                    if (link[-1] == '/'):
                        link = link[:-1]
                    if friends_name_key in jsonData:
                        friend_values = jsonData[friends_name_key]
                    else:
                        friend_values = []
                    friend_values.append({
                        'name': friend_name,
                        'link': link
                    })
                    jsonData[friends_name_key] = friend_values
                # json.dump(jsonData, f, ensure_ascii=False)
                # collection_currency = mydb['friends']
                # collection_currency.insert_one(jsonData)
                return jsonData
            if current_section == 4:
                friends_links = elements.find_elements_by_css_selector(".buofh1pr.hv4rvrfc")
                jsonData = {}
                for friends_link in friends_links:
                    friends_name_key = "friends_current_city"
                    friends_name = friends_link.find_element_by_css_selector(".oo9gr5id")
                    friend_name = friends_name.text
                    friend_link = friends_link.find_element_by_css_selector(".oajrlxb2")
                    link = friend_link.get_attribute("href")
                    link = create_original_link(link)
                    if (link[-1] == '/'):
                        link = link[:-1]
                    if friends_name_key in jsonData:
                        friend_values = jsonData[friends_name_key]
                    else:
                        friend_values = []
                    friend_values.append({
                        'name': friend_name,
                        'link': link
                    })
                    jsonData[friends_name_key] = friend_values
                # json.dump(jsonData, f, ensure_ascii=False)
                # collection_currency = mydb['friends']
                # collection_currency.insert_one(jsonData)
                return jsonData
            if current_section == 5:
                friends_links = elements.find_elements_by_css_selector(".buofh1pr.hv4rvrfc")
                jsonData = {}
                for friends_link in friends_links:
                    friends_name_key = "friends_hometown"
                    friends_name = friends_link.find_element_by_css_selector(".oo9gr5id")
                    friend_name = friends_name.text
                    friend_link = friends_link.find_element_by_css_selector(".oajrlxb2")
                    link = friend_link.get_attribute("href")
                    link = create_original_link(link)
                    if (link[-1] == '/'):
                        link = link[:-1]
                    if friends_name_key in jsonData:
                        friend_values = jsonData[friends_name_key]
                    else:
                        friend_values = []
                    friend_values.append({
                        'name': friend_name,
                        'link': link
                    })
                    jsonData[friends_name_key] = friend_values
                # json.dump(jsonData, f, ensure_ascii=False)
                # collection_currency = mydb['friends']
                # collection_currency.insert_one(jsonData)
                return jsonData
            # get names of friends
            # people_names = [
            #     x.find_element_by_tag_name("img").get_attribute("aria-label")
            #     for x in elements
            # ]

            # download friends' photos
            # try:
            #     if download_friends_photos:
            #         if friends_small_size:
            #             img_links = [
            #                 x.find_element_by_css_selector("img").get_attribute("src")
            #                 for x in elements
            #             ]
            #         else:
            #             links = []
            #             for friend in results:
            #                 try:
            #                     driver.get(friend)
            #                     WebDriverWait(driver, 30).until(
            #                         EC.presence_of_element_located(
            #                             (
            #                                 By.CLASS_NAME,
            #                                 selectors.get("profilePicThumb"),
            #                             )
            #                         )
            #                     )
            #                     l = driver.find_element_by_class_name(
            #                         selectors.get("profilePicThumb")
            #                     ).get_attribute("href")
            #                 except Exception:
            #                     l = "None"
            #
            #                 links.append(l)
            #
            #             for i, _ in enumerate(links):
            #                 if links[i] is None:
            #                     links[i] = "None"
            #                 elif links[i].find("picture/view") != -1:
            #                     links[i] = "None"
            #
            #             img_links = get_facebook_images_url(links)
            #
            #         folder_names = [
            #             "Friend's Photos",
            #             "Mutual Friends' Photos",
            #             "Following's Photos",
            #             "Follower's Photos",
            #             "Work Friends Photos",
            #             "College Friends Photos",
            #             "Current City Friends Photos",
            #             "Hometown Friends Photos",
            #         ]
            #         print("Downloading " + folder_names[current_section])
            #
            #         img_names = image_downloader(
            #             img_links, folder_names[current_section]
            #         )
            #     else:
            #         img_names = ["None"] * len(results)
            # except Exception:
            #     print(
            #         "Exception (Images)",
            #         str(status),
            #         "Status =",
            #         current_section,
            #         sys.exc_info()[0],
            #     )
        # dealing with Photos
        elif status == 1:
            div_box = elements.find_elements_by_class_name(
                selectors.get("a_href_img")
            )
            results = [x.get_attribute("href") for x in div_box]
            # results.pop(0)

            try:
                if download_uploaded_photos:
                    if photos_small_size:
                        background_img_links = driver.find_elements_by_xpath(
                            selectors.get("background_img_links")
                        )
                        background_img_links = [
                            x.get_attribute("style") for x in background_img_links
                        ]
                        background_img_links = [
                            ((x.split("(")[1]).split(")")[0]).strip('"')
                            for x in background_img_links
                        ]
                    else:
                        background_img_links = get_facebook_images_url(results)

                    folder_names = ["Uploaded Photos", "Tagged Photos"]
                    print("Downloading " + folder_names[current_section])

                    img_names = image_downloader(
                        background_img_links, folder_names[current_section],collection_name,status
                    )
                    # return img_names
                    return folder_names[current_section]
                    # return background_img_links
                else:
                    img_names = ["None"] * len(results)
            except Exception:
                print(
                    "Exception (Images)",
                    str(status),
                    "Status =",
                    current_section,
                    sys.exc_info()[0],
                )

        # dealing with Videos
        elif status == 2:
            results = elements[0].find_elements_by_css_selector("li")
            results = [
                x.find_element_by_css_selector("a").get_attribute("href")
                for x in results
            ]

            try:
                if results[0][0] == "/":
                    results = [r.pop(0) for r in results]
                    results = [(selectors.get("fb_link") + x) for x in results]
            except Exception:
                pass

        # dealing with About Section
        elif status == 3:
            if current_section == 0:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                for result in results:
                    parent_result = result.find_element_by_xpath('..')
                    title = "Tổng quan"
                    overviews_element = parent_result.find_elements_by_class_name("ii04i59q")
                    overviews = {}
                    for overview_element in overviews_element:

                        value_text = overview_element.text
                        overview_links = overview_element.find_elements_by_class_name("oajrlxb2")
                        link = ""
                        if len(overview_links) > 0:
                            overview_link = overview_links[0]
                            link = overview_link.get_attribute("href")
                        overviews[value_text] = link

                    jsonData[title] = overviews
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
            elif current_section == 1:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                for result in results:
                    parent_result = result.find_element_by_xpath('..')
                    title_element = parent_result.find_element_by_css_selector(".aahdfvyu.sej5wr8e")
                    title = title_element.text
                    works_element = parent_result.find_elements_by_css_selector(".ii04i59q.a3bd9o3v.jq4qci2q.oo9gr5id")
                    works = {}
                    if len(works_element) > 0:
                        for work in works_element:
                            name_adress_key = "Địa điểm"
                            value_text = work.text
                            works_links = work.find_elements_by_css_selector(".oajrlxb2")
                            link = ""
                            if len(works_links) > 0:
                                work_link = works_links[0]
                                link = work_link.get_attribute("href")

                            if name_adress_key in works:
                                work_values = works[name_adress_key]
                            else:
                                work_values =[]
                            work_values.append({
                                'name': value_text,
                                'link': link
                            })
                            works[name_adress_key] = work_values
                    else:
                        name_adress_key = "Địa điểm"
                        work_values = "Không có địa điểm để hiển thị"
                        works[name_adress_key] = work_values
                    jsonData[title] = works
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
            elif current_section == 2:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                for result in results:
                    parent_result = result.find_element_by_xpath('..')
                    title_element = parent_result.find_element_by_css_selector(".aahdfvyu.sej5wr8e")
                    title = title_element.text
                    places_live_element = parent_result.find_elements_by_css_selector(".g5gj957u")
                    place_live_values = {}
                    for place_live_element in places_live_element:
                        name_place_live = place_live_element.find_element_by_css_selector(".j5wam9gi")
                        place_live_key = name_place_live.text
                        place_live_value = place_live_element.find_element_by_class_name("nc684nl6")
                        value_text = place_live_value.text
                        place_live_links = place_live_element.find_elements_by_class_name("oajrlxb2")
                        link = ""
                        if len(place_live_links) > 0:
                            place_live_link = place_live_links[0]
                            link = place_live_link.get_attribute("href")
                        if place_live_key in place_live_values:
                            place_live = place_live_values[place_live_key]
                        else:
                            place_live = []
                        place_live.append({
                            'name': value_text,
                            'link': link
                        })
                        place_live_values[place_live_key] = place_live
                    jsonData[title] = place_live_values
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
            elif current_section == 3:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                for result in results:
                    parent_result = result.find_element_by_xpath('..')
                    title_element = parent_result.find_element_by_css_selector(".aahdfvyu.sej5wr8e")
                    title = title_element.text
                    infos_element = parent_result.find_elements_by_class_name("g5gj957u")
                    basic_infos = {}
                    for info_element in infos_element:
                        name_info_element = info_element.find_element_by_class_name("m9osqain")
                        name_info_key = name_info_element.text
                        name_info_values = info_element.find_elements_by_class_name("oo9gr5id")
                        value_text = ""
                        if len(name_info_values) > 0:
                            name_info_value = name_info_values[0]
                            value_text = name_info_value.text
                        basic_infos[name_info_key] = value_text

                    jsonData[title] = basic_infos
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
            elif current_section == 4:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                for result in results:
                    parent_result = result.find_element_by_xpath('..')
                    title_element = parent_result.find_element_by_css_selector(".aahdfvyu.sej5wr8e")
                    title = title_element.text
                    relationships_element = parent_result.find_elements_by_css_selector(".g5gj957u")
                    relationships = {}
                    for relationship_element in relationships_element:
                        name_relationship = relationship_element.find_elements_by_class_name("m9osqain")
                        name_relationship_key = "Tình trạng"
                        if len(name_relationship) > 0:
                            z = name_relationship[0]
                            name_relationship_key = z.text
                        name_relationship_values = relationship_element.find_elements_by_class_name("ii04i59q")
                        value_text = ""
                        if len(name_relationship_values) > 0:
                            name_relationship_value = name_relationship_values[0]
                            value_text = name_relationship_value.text

                        relationship_links = relationship_element.find_elements_by_class_name("oajrlxb2")
                        link = ""
                        if len(relationship_links) > 0:
                            relationship_link = relationship_links[0]
                            link = relationship_link.get_attribute("href")
                        if name_relationship_key in relationships:
                            relationship_values = relationships[name_relationship_key]
                        else:
                            relationship_values =[]
                        relationship_values.append({
                            'name': value_text,
                            'link': link
                        })
                        relationships[name_relationship_key] = relationship_values

                    jsonData[title] = relationships
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
            elif current_section == 5:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                for result in results:
                    parent_result = result.find_element_by_xpath('..')
                    title_element = parent_result.find_element_by_css_selector(".aahdfvyu.sej5wr8e")
                    title = title_element.text
                    details_element = parent_result.find_elements_by_css_selector(".g5gj957u")
                    details = {}
                    for detail_element in details_element:
                        name_detail_elements = detail_element.find_elements_by_class_name("m9osqain")
                        name_detail_key = "Tên"
                        if len(name_detail_elements) > 0:
                            name_detail_element = name_detail_elements[0]
                            name_detail_key = name_detail_element.text

                        name_detail_values = detail_element.find_elements_by_class_name("oo9gr5id")
                        value_text = ""
                        if len(name_detail_values) > 0:
                            name_detail_value = name_detail_values[0]
                            value_text = name_detail_value.text
                        if name_detail_key in details:
                            name_details = details[name_detail_key]
                        else:
                            name_details = []
                        name_details.append(value_text)
                        details[name_detail_key] = name_details

                    jsonData[title] = details
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
            elif current_section == 6:
                element = elements.find_element_by_css_selector(".dati1w0a.tu1s4ah4.f7vcsfb0.discj3wi")
                results = element.find_elements_by_css_selector(".aahdfvyu.sej5wr8e")
                jsonData = {}
                if len(results) > 0:
                    for result in results:
                        parent_result = result.find_element_by_xpath('..')
                        title_element = parent_result.find_element_by_css_selector(".aahdfvyu.sej5wr8e")
                        title = title_element.text
                        events_element = parent_result.find_elements_by_class_name("g5gj957u")
                        events = {}
                        for event_element in events_element:
                            name_event_key = "Sự kiện"
                            name_event_value = event_element.find_element_by_class_name("oo9gr5id")
                            value_text = name_event_value.text
                            events_link = event_element.find_elements_by_class_name("oajrlxb2")
                            link = ""
                            if len(events_link) > 0:
                                event_link = events_link[0]
                                link = event_link.get_attribute("href")
                            if name_event_key in events:
                                events_values = events[name_event_key]
                            else:
                                events_values = []
                            events_values.append({
                                'name': value_text,
                                'link': link
                            })
                            events[name_event_key] = events_values
                        jsonData[title] = events
                else:
                    title = "Không có sự kiện trong đời để hiển thị"
                    events = ""
                    jsonData[title] = events
                # json.dump(jsonData, f, ensure_ascii=False)
                return jsonData
        # dealing with Posts
        elif status == 4:

            # post_lists = elements.find_elements_by_css_selector(".du4w35lb.k4urcfbm.l9j0dhe7.sjgh65i0")
            post_lists = elements
            item = "Posts"
            name = "Posts.json"
            data_post = extract_and_write_posts(post_lists, name, collection_name, item)
            return data_post

        # dealing with Group Posts
        elif status == 5:
            div_box = elements.find_elements_by_class_name(
                selectors.get("a_href_img")
            )
            results = [x.get_attribute("href") for x in div_box]
            # results.pop(0)

            try:
                if download_uploaded_photos:
                    if photos_small_size:
                        background_img_links = driver.find_elements_by_xpath(
                            selectors.get("background_img_links")
                        )
                        background_img_links = [
                            x.get_attribute("style") for x in background_img_links
                        ]
                        background_img_links = [
                            ((x.split("(")[1]).split(")")[0]).strip('"')
                            for x in background_img_links
                        ]
                    else:
                        background_img_links = get_facebook_images_url(results)

                    folder_names = ["Uploaded Photos", "Tagged Photos"]
                    print("Downloading " + folder_names[current_section])
                    img_names = image_downloader(
                        background_img_links, folder_names[current_section], collection_name, status
                    )
                else:
                    img_names = ["None"] * len(results)
            except Exception:
                print(
                    "Exception (Images)",
                    str(status),
                    "Status =",
                    current_section,
                    sys.exc_info()[0],
                )

        """Write results to file"""
        # if status == 0:
        #     for i, _ in enumerate(results):
        #         # friend's profile link
        #         f.writelines(results[i])
        #         f.write(",")
        #
        #         # friend's name
        #         # f.writelines(people_names[i])
        #         f.write(",")
        #
        #         # friend's downloaded picture id
        #         f.writelines(img_names[i])
        #         f.write("\n")

        if status == 1:
            for i, _ in enumerate(results):
                # image's link
                f.writelines(results[i])
                f.write(",")

                # downloaded picture id
                f.writelines(img_names[i])
                f.write("\n")

        elif status == 2:
            for x in results:
                f.writelines(x + "\n")

        f.close()

    except Exception:
        print("Exception (save_to_file)", "Status =", str(status), sys.exc_info()[0])
def get_account_id():
    try:
        user_id_element = driver.find_element_by_css_selector(".oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.a8c37x1j.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.d5it6em2.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.l9j0dhe7.abiwlrkh.p8dawk7l.k4urcfbm")
        user_id = user_id_element.get_attribute("href")
        user_id = user_id.split(".")[-1]
        user_name_element = driver.find_element_by_css_selector(".gmql0nx0.l94mrbxd.p1ri9a11.lzcic4wl.bp9cbjyn.j83agx80")
        user_name = user_name_element.get_attribute('innerText')
        user_name = user_name.split("\n")[0]
        return user_id,user_name
    except:
        print("Do not find profile")
# ----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def scrape_data(url, scan_list, section, elements_path, save_status, file_names,collection_name):
    """Given some parameters, this function can scrap friends/photos/videos/about/posts(statuses) of a profile"""
    # with open("D:/crawler_fb/Ultimate-Facebook-Scraper/credentials.yaml", "r") as ymlfile:
    #     cfg = yaml.safe_load(stream=ymlfile)
    if ("path" not in cfg):
        print("Not Path")
        exit(1)
    root_path = cfg["path"]
    page = []
    if save_status == 4:
        page.append(url)
    page += [url + s for s in section]
    # checkclone = url.find("id")
    # if(checkclone == -1):
    #     page += [url + s for s in section]
    # else:
    #     for x in section:
    #         x = x.replace('/', '')
    #         page += url+'&sk='+x
    dataColect = {}
    res = {}
    list_currentimg = []
    for i, _ in enumerate(scan_list):
        try:
            if(save_status != 4):
                driver.get(page[i])
            sleep(random.randint(3,10))
            if (
                (save_status == 0) or (save_status == 1) or (save_status == 2)
            ):  # Only run this for friends, photos and videos

                # the bar which contains all the sections
                # sections_bar = driver.find_element_by_xpath(
                #     selectors.get("sections_bar")
                # )
                #
                # if sections_bar.text.find(scan_list[i]) == -1:
                #     continue
                A = 1
            if(save_status == 4):
                listID = list()
                mycol = mydb[collection_name]
                documents = mycol.find()
                for x in documents:
                    if ('Posts' in x.keys()):
                        list_post = x.get('Posts')
                        for post in list_post:
                            id_post = post.get('post_id')
                            listID.append(id_post)
                link = utils.scroll_post(total_scrolls, driver, listID)
                data = link
            elif save_status != 3:
                utils.scroll(total_scrolls, driver, selectors, scroll_time)
                data = driver.find_element_by_xpath(elements_path[i])

            # link = driver.find_elements_by_xpath('//*[@id!=""]/span[2]/span/a')
            # for i in link:
            #     hover = ActionChains(driver).move_to_element(i)
            #     hover.perform()

            _data = save_to_file( file_names[i], data, save_status, i,collection_name)
            if(save_status != 1):
                if(dataColect == {}):
                    dataColect = _data
                else:
                    dataColect.update(_data)
            else:
                list_currentimg.append(_data)
        except Exception:
            print(
                "Exception (scrape_data)",
                str(i),
                "Status =",
                str(save_status),
                sys.exc_info()[0],
            )
    try:
        collection_currency = mydb[collection_name]
        listcol = mydb.list_collection_names()
        if(collection_name in listcol):
            document = collection_currency.find()
            doccount = collection_currency.count_documents({})
            i = 0
            if (save_status == 4):
                res['Posts'] = dataColect
                for item in document:
                    i = i + 1
                    if ('Posts' in item.keys()):
                        id = item.get('_id')
                        count = len(item.get('Posts'))
                        index = 0
                        for i in dataColect:
                            mycol.update({'_id': id}, {'$set': {"Posts." + str(count + index): i}})
                            index += 1
                        # collection_currency.update_one({'_id': id}, {'$set': res})
                        break
                    elif (i == doccount):
                        collection_currency.insert_one(res)
            elif(save_status == 3):
                res['About'] = dataColect
                for item in document:
                    i = i+1
                    if ('About' in item.keys()):
                        id = item.get('_id')
                        collection_currency.update_one({'_id': id}, {'$set': res})
                        break
                    elif(i == doccount):
                        collection_currency.insert_one(res)
            elif(save_status == 0):
                res['Friends'] = dataColect
                for item in document:
                    i = i + 1
                    if ('Friends' in item.keys()):
                        id = item.get('_id')
                        collection_currency.update_one({'_id': id}, {'$set': res})
                        break
                    elif (i == doccount):
                        collection_currency.insert_one(res)
            elif(save_status == 1):
                list_img = {}
                list_allimg = {}
                for folder_img in list_currentimg:
                    path_img = collection_name+r"/Photos/"+folder_img
                    root_path_img = root_path+"/data/"+path_img
                    root_path_img = root_path_img.replace('"','')
                    for path in os.listdir(root_path_img):
                        full_path = os.path.join(root_path_img, path)
                        if os.path.isfile(full_path):
                            Img_name_key = folder_img
                            if Img_name_key in list_img:
                                string_va = list_img[Img_name_key]
                            else:
                                string_va = []
                            string_va.append({
                                'name': path,
                                'link': full_path
                            })
                            list_img[Img_name_key] = string_va
                    if (list_allimg == {}):
                        list_allimg = list_img
                    else:
                        list_allimg.update(list_img)
                res['Photos'] = list_allimg
                for item in document:
                    i = i + 1
                    if ('Photos' in item.keys()):
                        id = item.get('_id')
                        collection_currency.update_one({'_id': id}, {'$set': res})
                        break
                    elif (i == doccount):
                        collection_currency.insert_one(res)
                # for item in _data:
                #     data_img = get_as_base64(item)
                #     name = (item.split(".jpg")[0]).split("/")[-1] + ".jpg"
                #     friends_name_key = "Uploaded Photos"
                #     if friends_name_key in list_img:
                #         string_va = list_img[friends_name_key]
                #     else:
                #         string_va = []
                #     string_va.append({
                #         'name': name,
                #         'link': data_img.decode('utf-8')
                #     })
                #     list_img[friends_name_key] = string_va
                # res['Images'] = list_img
                # if doccount == 0 :
                #     collection_currency.insert_one(res)
                # else:
                #     for item in document:
                #         i = i+1
                #         if ('Images' in item.keys()):
                #             id = item.get('_id')
                #             collection_currency.update_one({'_id': id}, {'$set': res})
                #             break
                #         elif(i == doccount):
                #             collection_currency.insert_one(res)
        else:
            if (save_status == 4):
                res['Posts'] = dataColect
                collection_currency.insert_one(res)
            elif (save_status == 3):
                res['About'] = dataColect
                collection_currency.insert_one(res)
            elif (save_status == 0):
                res['Friends'] = dataColect
                collection_currency.insert_one(res)
            elif (save_status == 1):
                list_allimg = {}
                for folder_img in list_currentimg:
                    list_img = {}
                    path_img = collection_name + r"/Photos/" + folder_img
                    root_path_img = root_path + "/data/" + path_img
                    root_path_img = root_path_img.replace('"', '')
                    for path in os.listdir(root_path_img):
                        full_path = os.path.join(root_path_img, path)
                        if os.path.isfile(full_path):
                            Img_name_key = folder_img
                            if Img_name_key in list_img:
                                string_va = list_img[Img_name_key]
                            else:
                                string_va = []
                            string_va.append({
                                'name': path,
                                'link': full_path
                            })
                            list_img[Img_name_key] = string_va
                    if (list_allimg == {}):
                        list_allimg = list_img
                    else:
                        list_allimg.update(list_img)
                res['Photos'] = list_allimg
                collection_currency.insert_one(res)
    except:
        print("Something went wrong while saving")
    return

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def create_original_link(url):
    if url.find(".php") != -1:
        original_link = (
            facebook_https_prefix + facebook_link_body + ((url.split("="))[1])
        )

        if original_link.find("&") != -1:
            original_link = original_link.split("&")[0]

    elif url.find("fnr_t") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + ((url.split("/"))[-1].split("?")[0])
        )
    elif url.find("_tab") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + (url.split("?")[0]).split("/")[-1]
        )
    else:
        original_link = url

    return original_link


def scrap_profile():
    # with open("../credentials.yaml", "r") as ymlfile:
    #     cfg = yaml.safe_load(stream=ymlfile)
    if ("path" not in cfg):
        print("Not Path")
        exit(1)
    path = cfg["path"]
    data_folder = os.path.join(path, "data")
    utils.create_folder(data_folder)
    # os.chdir(data_folder)

    # execute for all profiles given in input.txt file
    url = driver.current_url
    user_id = create_original_link(url)
    collection_name = user_id.split("/")[-1]
    print("\nScraping:", user_id)

    try:
        target_dir = os.path.join(data_folder, user_id.split("/")[-1])
        utils.create_folder(target_dir)
        # os.chdir(target_dir)
    except Exception:
        print("Some error occurred in creating the profile directory.")
        # os.chdir("../..")
        return

    to_scrap = ["Posts"]
    for item in to_scrap:
        # values = None
        # mycol = mydb[collection_name]
        # document = mycol.find()
        # for x in document:
        #     key = x.keys()
        #     for i in key:
        #         if(i == item):
        #             values = x.get(item)
        #             break
        # if(values != None and values != {}):
        #     continue
        if(item == 'Photos'):
            folder = os.path.join(target_dir, item)
            utils.create_folder(folder)
        if (item == 'Posts'):
            folder = os.path.join(target_dir, item)
            utils.create_folder(folder)
            # os.chdir(folder)
        print("----------------------------------------")
        print("Scraping {}..".format(item))

        if item == "Posts":
            scan_list = [None]
        elif item == "About":
            scan_list = [None] * 7
        else:
            if url.find(".php") == -1:
                scan_list = params[item][0]["scan_list"]
            else:
                scan_list = params[item][1]["scan_list"]
        if url.find(".php") == -1:
            section = params[item][0]["section"]
            elements_path = params[item][0]["elements_path"]
            file_names = params[item][0]["file_names"]
            save_status = params[item][0]["save_status"]
        else:
            section = params[item][1]["section"]
            elements_path = params[item][1]["elements_path"]
            file_names = params[item][1]["file_names"]
            save_status = params[item][1]["save_status"]
        sleep(random.randint(3,5))
        scrape_data(url, scan_list, section, elements_path, save_status, file_names,collection_name)
        print("{} Done!".format(item))

    print("Finished Scraping Profile " + str(user_id) + ".")
    # os.chdir("../..")

    return


def get_comments():
    comments = []
    try:
        data = driver.find_element_by_xpath(selectors.get("comment_section"))
        reply_links = driver.find_elements_by_xpath(
            selectors.get("more_comment_replies")
        )
        for link in reply_links:
            try:
                driver.execute_script("arguments[0].click();", link)
            except Exception:
                pass
        see_more_links = driver.find_elements_by_xpath(
            selectors.get("comment_see_more_link")
        )
        for link in see_more_links:
            try:
                driver.execute_script("arguments[0].click();", link)
            except Exception:
                pass
        data = data.find_elements_by_xpath(selectors.get("comment"))
        for d in data:
            try:
                author = d.find_element_by_xpath(selectors.get("comment_author")).text
                text = d.find_element_by_xpath(selectors.get("comment_text")).text
                replies = utils.get_replies(d, selectors)
                comments.append([author, text, replies])
            except Exception:
                pass
    except Exception:
        pass
    return comments


def get_group_post_as_line(post_id, photos_dir):
    try:
        data = driver.find_element_by_xpath(selectors.get("single_post"))
        time = utils.get_time(data)
        title = utils.get_title(data, selectors).text
        # link, status, title, type = get_status_and_title(title,data)
        link = utils.get_div_links(data, "a", selectors)
        if link != "":
            link = link.get_attribute("href")
        post_type = ""
        status = '"' + utils.get_status(data, selectors).replace("\r\n", " ") + '"'
        photos = utils.get_post_photos_links(data, selectors, photos_small_size)
        comments = get_comments()
        photos = image_downloader(photos, photos_dir)
        line = (
            str(time)
            + "||"
            + str(post_type)
            + "||"
            + str(title)
            + "||"
            + str(status)
            + "||"
            + str(link)
            + "||"
            + str(post_id)
            + "||"
            + str(photos)
            + "||"
            + str(comments)
            + "\n"
        )
        return line
    except Exception:
        return ""


def create_folders():
    """
    Creates folder for saving data (profile, post or group) according to current driver url
    Changes current dir to target_dir
    :return: target_dir or None in case of failure
    """
    path = cfg["path"]
    folder = os.path.join(path, "data")
    utils.create_folder(folder)
    # os.chdir(folder)
    try:
        item_id = get_item_id(driver.current_url)
        target_dir = os.path.join(folder, item_id)
        utils.create_folder(target_dir)
        # os.chdir(target_dir)
        return target_dir
    except Exception:
        print("Some error occurred in creating the group directory.")
        # os.chdir("../..")
        return None
def create_folders_group():

    if ("path" not in cfg):
        print("Not Path")
        exit(1)
    path = cfg["pathgroup"]
    data_group = os.path.join(path, "data")
    utils.create_folder(data_group)
    try:
        item_id = get_item_id(driver.current_url).split("/")[-1]
        target_dir = os.path.join(data_group, item_id)
        utils.create_folder(target_dir)
        # os.chdir(target_dir)
        return target_dir
    except Exception:
        print("Some error occurred in creating the group directory.")
        os.chdir("../..")
        return None

def get_item_id(url):
    """
    Gets item id from url
    :param url: facebook url string
    :return: item id or empty string in case of failure
    """
    ret = ""
    try:
        link = create_original_link(url)
        ret = link
        if ret.strip() == "":
            ret = link.split("/")[-2]
    except Exception as e:
        print("Failed to get id: " + format(e))
    return ret


def scrape_group(url):
    if create_folders_group() is None:
        return

    group_id = get_item_id(url).split("/")[-1]
    # execute for all profiles given in input.txt file
    print("\nScraping:", group_id)

    to_scrap = ["GroupPhotos"]# , "Photos", "Videos", "About"]
    for item in to_scrap:
        folder = os.path.join(create_folders_group(), item)
        utils.create_folder(folder)
        print("----------------------------------------")
        print("Scraping {}..".format(item))

        if item == "GroupPosts":
            scan_list = [None]
        elif item == "About":
            scan_list = [None] * 7
        else:
            scan_list = params[item]["scan_list"]

        section = params[item]["section"]
        elements_path = params[item]["elements_path"]
        file_names = params[item]["file_names"]
        save_status = params[item]["save_status"]

        scrape_data(url, scan_list, section, elements_path, save_status, file_names, group_id)

        print("{} Done!".format(item))

    print("Finished Scraping Group " + str(group_id) + ".")
    os.chdir("../..")

    return


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def login(email, password):
    """ Logging into our own profile """

    try:
        global driver
        # filling the form
        driver.find_element_by_name("email").send_keys(email)
        driver.find_element_by_name("pass").send_keys(password)

        try:
            # clicking on login button
            driver.find_element_by_id("loginbutton").click()
            sleep(random.randint(5,15))
        except NoSuchElementException:
            # Facebook new design
            driver.find_element_by_name("login").click()

        # if your account uses multi factor authentication
        mfa_code_input = utils.safe_find_element_by_id(driver, "approvals_code")

        if mfa_code_input is None:
            return

        mfa_code_input.send_keys(input("Enter MFA code: "))
        driver.find_element_by_id("checkpointSubmitButton").click()

        # there are so many screens asking you to verify things. Just skip them all
        while (
            utils.safe_find_element_by_id(driver, "checkpointSubmitButton") is not None
        ):
            dont_save_browser_radio = utils.safe_find_element_by_id(driver, "u_0_3")
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            driver.find_element_by_id("checkpointSubmitButton").click()

    except Exception:
        print("There's some error in log in.")
        print(sys.exc_info()[0])
        exit(1)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def list_friends(collection_name):
    urls = []
    try:
        list_collections = mydb.list_collection_names()
        collection_name = collection_name.replace('\r\n', '')
        print(collection_name)
        mycol = mydb[collection_name]
        document = mycol.find()
        for x in document:
            if ('Friends' in x.keys()):
                value = x.get('Friends')
                friendkey = ['All_friend', 'following', 'followers', 'friends_college', 'friends_current_city',
                             'friends_hometown']
                for item in friendkey:
                    data_value = value.get(item)
                    if (data_value != None):
                        for i in data_value:
                            link = i.get('link')
                            id = link.find("id")
                            urls.append(link)
        return urls
    except:
        print("Not connect DB")
def scrap_secursion(urls):
    # print(urls)
    arrUser_Id = {}
    for url in urls:
        col_name = url.split("/")[-1]
        list_collections = mydb.list_collection_names()
        # if(col_name in list_collections):
        #     continue
        if(url[-1] == '/'):
            url = url[:-1]
        driver.get(url)
        sleep(random.randint(3, 7))
        driver.execute_script("window.scrollTo(0, 200)")
        sleep(random.randint(1,3))

        try:
            account_id, account_name = get_account_id()
            account = []
            account.append({"user_id": account_id})
            account.append({"user_name": account_name})
            mycol = mydb[col_name]
            listcol = mydb.list_collection_names()
            if (col_name in listcol):
                document = mycol.find()
                doccount = mycol.count_documents({})
                i = 0
                arrUser_Id['UserID'] = account
                for item in document:
                    i = i + 1
                    if ('UserID' in item.keys()):
                        id = item.get('_id')
                        mycol.update_one({'_id': id}, {'$set': arrUser_Id})
                        break
                    elif (i == doccount):
                        mycol.insert_one(arrUser_Id)
            else:
                arrUser_Id['UserID'] = account
                mycol.insert_one(arrUser_Id)
        except:
            print("co loi trong qua trinh luu ID va Ten")
        link_type = utils.identify_url(driver.current_url)
        if link_type == 0:
            scrap_profile()
            sleep(random.randint(5,10))

            # listfr = list_friends(col_name)
            # if(listfr != None):
            #     urls = urls + list_friends(col_name)
            urls.remove(url)
            if(len(urls)>0):
                scrap_secursion(urls)
        elif link_type == 1:
            # scrap_post(url)
            pass
        elif link_type == 2:
            scrape_group(driver.current_url)
        elif link_type == 3:
            file_name = params["GroupPosts"]["file_names"][0]
            item_id = get_item_id(driver.current_url)
            if create_folders() is None:
                continue
            f = create_post_file(file_name)
            add_group_post_to_file(f, file_name, item_id)
            f.close()
            # os.chdir("../..")
def scraper(**kwargs):
    if ("password" not in cfg) or ("email" not in cfg):
        print("Your email or password is missing. Kindly write them in credentials.txt")
        exit(1)
    urls = [
        get_item_id(line)
        for line in open("../input.txt", newline="\r\n")
        if not line.lstrip().startswith("#") and not line.strip() == ""
    ]

    #doan nay de check db
    # urls = []
    # myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    # db = myclient["data_fb"]
    # list_col = db.list_collection_names()
    # uri = "https://www.facebook.com/"
    # for col in list_col:
    #     mycol = db[col]
    #     documents = mycol.find()
    #     for x in documents:
    #         if ('Posts' in x.keys()):
    #             value = x.get('Posts')
    #             if (value == []):
    #                 link = uri + str(col)
    #                 if (link not in urls):
    #                     urls.append(link)
    #             else:
    #                 if (link in urls):
    #                     urls.remove(link)
    #         else:
    #             link = uri + str(col)
    #             if(link not in urls):
    #                 urls.append(link)
    # user_id = create_original_link(urls[0])
    # if(urls[0].find("/n") != -1):
    #     urls[0].replace('/n','')

    # collection_name = user_id.split("/")[-1]
    # list_friend = list_friends(collection_name)
    # if(list_friend != None):
    #     urls = urls + list_friend
    if len(urls) > 0:
        print(len(urls))
        print("\nStarting Scraping...")
        # login(cfg["email"], cfg["password"])
        # sleep(random.randint(5,15))
        # for url in urls:
        #     col_name = url.split("/")[-1]
        #     # if(col_name in list_collections):
        #     #     continue
        #     driver.get(url)
        #     link_type = utils.identify_url(driver.current_url)
        #     if link_type == 0:
        #         # scrap_profile()
        #         # sleep(random.randint(5,10))
        #         urls = urls + list_friends(col_name)
        #         print(urls)
        #     elif link_type == 1:
        #         # scrap_post(url)
        #         pass
        #     elif link_type == 2:
        #         scrape_group(driver.current_url)
        #     elif link_type == 3:
        #         file_name = params["GroupPosts"]["file_names"][0]
        #         item_id = get_item_id(driver.current_url)
        #         if create_folders() is None:
        #             continue
        #         f = create_post_file(file_name)
        #         add_group_post_to_file(f, file_name, item_id)
        #         f.close()
        #         os.chdir("../..")
        scrap_secursion(urls)
        # driver.close()
    else:
        print("Input file is empty.")

# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["data_crawlFB"]
link_root = "https://facebook.com/"

app=Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
@app.route('/post', methods=['GET', 'POST'])
def GetPost():
    # get things rolling
    scraper()

@app.route('/listUser', methods=['GET', 'POST'])
def listUser():
    reques_data = request.data
    dict_str = reques_data.decode("UTF-8")
    reques_data = ast.literal_eval(dict_str)
    p = int(reques_data.get("p"))
    pz = int(reques_data.get("pz"))
    size = pz*p
    p = size - pz
    list_col = db.list_collection_names()
    list_data = list()
    list_user = {}
    count = {}
    list_result = list()
    index = 0
    for col in list_col:
        check = False
        index += 1
        if(index > size):
            break
        data_user = {}
        mycol = db[col]
        documents = mycol.find()
        for x in documents:
            if ('UserID' in x.keys()):
                check = True
                value = x.get('UserID')
                if (value != [] and type(value) != str and value != None):
                    id = value[0].get("user_id")
                    if (id != None):
                        link = link_root + str(id)
                        data_user["link"] = link
                    else:
                        link = link_root + str(col)
                        data_user["link"] = link
                    name = value[1].get("user_name")
                    data_user["name"] = name
                    data_user["id"] = col
                    list_data.append(data_user)
                else:
                    link = link_root + str(col)
                    data_user["link"] = link
                    data_user["id"] = col
                    list_data.append(data_user)
        if(check == False):
            link = link_root + str(col)
            data_user["link"] = link
            data_user["id"] = col
            list_data.append(data_user)
    list_user["listUser"] = list_data[p:size]
    count["count"] = len(list_col)
    list_result.append(list_user)
    list_result.append(count)
    return json.dumps(list_result)

@app.route('/listFriend', methods=['GET', 'POST'])
def listFriend():
    reques_data = request.data
    dict_str = reques_data.decode("UTF-8")
    reques_data = ast.literal_eval(dict_str)
    p = int(reques_data.get("p"))
    pz = int(reques_data.get("pz"))
    col = reques_data.get("col")
    count = {}
    size = pz*p
    p = size - pz
    mycol = db[col]
    list_result = list()
    list_data = {}
    All_friends = list()
    documents = mycol.find()
    for x in documents:
        if ('Friends' in x.keys()):
            value = x.get('Friends')
            All_friends = value.get("All_friend")
    if(size > len(All_friends)):
        size = len(All_friends)
    list_data["listFriend"] = All_friends[p:size]
    count["count"] = len(All_friends)
    list_result.append(list_data)
    list_result.append(count)
    return json.dumps(list_result)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    # PLS CHECK IF HELP CAN BE BETTER / LESS AMBIGUOUS
    ap.add_argument(
        "-dup",
        "--uploaded_photos",
        help="download users' uploaded photos?",
        default=True,
    )
    ap.add_argument(
        "-dfp", "--friends_photos", help="download users' photos?", default=True
    )
    ap.add_argument(
        "-fss",
        "--friends_small_size",
        help="Download friends pictures in small size?",
        default=True,
    )
    ap.add_argument(
        "-pss",
        "--photos_small_size",
        help="Download photos in small size?",
        default=True,
    )
    ap.add_argument(
        "-ts",
        "--total_scrolls",
        help="How many times should I scroll down?",
        default=2500,
    )
    ap.add_argument(
        "-st", "--scroll_time", help="How much time should I take to scroll?", default=8
    )

    args = vars(ap.parse_args())

    # ---------------------------------------------------------
    # Global Variables
    # ---------------------------------------------------------

    # whether to download photos or not
    download_uploaded_photos = utils.to_bool(args["uploaded_photos"])
    download_friends_photos = utils.to_bool(args["friends_photos"])

    # whether to download the full image or its thumbnail (small size)
    # if small size is True then it will be very quick else if its false then it will open each photo to download it
    # and it will take much more time
    friends_small_size = utils.to_bool(args["friends_small_size"])
    photos_small_size = utils.to_bool(args["photos_small_size"])

    total_scrolls = int(args["total_scrolls"])
    scroll_time = int(args["scroll_time"])

    current_scrolls = 0
    old_height = 0

    driver = None

    with open("../selectors.json") as a, open("../params.json") as b:
        selectors = json.load(a)
        params = json.load(b)

    firefox_profile_path = selectors.get("firefox_profile_path")
    facebook_https_prefix = selectors.get("facebook_https_prefix")
    facebook_link_body = selectors.get("facebook_link_body")

    options = Options()

    #  Code to disable notifications pop up of Chrome Browser
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    # options.add_argument("headless")

    try:
        for i in range(1):
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )
            fb_path = facebook_https_prefix + facebook_link_body
            driver.get(fb_path)
            driver.maximize_window()
            login(cfg["email_bot"+str(i)], cfg["password_bot"+str(i)])
            sleep(random.randint(1, 5))
            logging.debug("dang nhap thanh cong: " + cfg["email_bot"+str(i)])
            scraper()
    except Exception as ex:
        logging.debug("Loi khoi tao chrome driver" + sys.exc_info()[0])
        # print("Error loading chrome webdriver " + sys.exc_info()[0])
        exit(1)
    app.run(host=cfg["ip"], port=cfg["port"])
