#!/usr/bin/python3

import argparse
import logging
import sys
import os
from datetime import datetime
import math
import random
import shutil

from PIL import Image, TiffImagePlugin
import matplotlib.pyplot as plt
import pandas as pd

from config import LOGS_FOLDER_NAME, LOGS_FORMAT
from config import IMG_EXTENSION
from config import PATH_DATASET

from keras import applications
from keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
from keras.utils.np_utils import to_categorical
import numpy as np


def valid_fetch(args):
    return args.fetch and args.csv and args.path


def valid_new_trainset(args):
    return args.new_trainset and args.train and args.validate


def validate_args(args):
    return valid_fetch(args) or valid_new_trainset(args)


def find_repeated(df):
    logging.debug('\n' + str(df.nunique()))
    count_movements_in_authors = df.groupby('author')['movement'].nunique().reset_index(name='count')
    one_movement_author = count_movements_in_authors.loc[count_movements_in_authors['count'] == 1]['author']
    valid_dataset = df.loc[df.author.isin(list(one_movement_author))]
    logging.debug('\n' + str(valid_dataset.nunique()))
    logging.info('Lost ' + str(df.nunique()['id'] - valid_dataset.nunique()['id']) + ' paintings.')
    return valid_dataset


def get_sizes(df, path, most_frequent_movements):
    total = (0, 0)
    count = 0
    min_width = float('inf')
    min_height = float('inf')
    images_eq = []
    images_wgth = []
    images_hgtw = []
    for mov in list(most_frequent_movements['movement']):
        for img in list(df.loc[df['movement'] == mov]['id']):
            try:
                infile = os.path.join(path, img + IMG_EXTENSION)
                im = Image.open(infile)
                (width, height) = im.size

                if width < height:
                    images_hgtw.append(img)
                elif height < width:
                    images_wgth.append(img)
                else:
                    images_eq.append(img)

                min_width = min(min_width, width)
                min_height = min(min_height, height)
                total = (total[0] + width, total[1] + height)
                count += 1
            except Exception as ex:
                pass

    logging.info("min width value: " + str(min_width))
    logging.info("min height value: " + str(min_height))
    logging.info('average width value: ' + str(math.floor(total[0] / count)))
    logging.info('average height value: ' + str(math.floor(total[1] / count)))
    logging.info('total number of images: ' + str(count))
    logging.info('total number of images with width greater than height: ' + str(len(images_wgth)))
    logging.info('total number of images with height greater than width: ' + str(len(images_hgtw)))
    logging.info('total number of images with width equals to height: ' + str(len(images_eq)))


    return [math.floor(min_width), math.floor(min_height)]


def fetch(path, csv):
    TiffImagePlugin.DEBUG = False

    df = pd.read_csv(csv)

    # Buscamos repetidos
    df = find_repeated(df)

    pd_of_times = df.groupby('time')['movement','painting_name'].nunique().sort_values('movement', ascending=False)

    logging.debug('\n' + str(pd_of_times))

    best_time_name = pd_of_times.iloc[:,0].index[0]
    best_time_number_movements = pd_of_times.iloc[0][0]
    best_time_number_paintings = pd_of_times.iloc[0][1]

    logging.info('The best time is ' + str(best_time_name) + ' with ' + str(best_time_number_paintings)
                 + ' paintings and ' + str(best_time_number_movements) + ' movements.')

    most_frequent_movement_from_best_time = df.loc[df['time'] == best_time_name].groupby('movement')[
                                                'painting_name'].nunique().reset_index(
        name='num_paintings').sort_values('num_paintings', ascending=False)[:20]

    logging.debug('\n' + str(most_frequent_movement_from_best_time))

    size = get_sizes(df, path, most_frequent_movement_from_best_time)

    images = get_list_of_images(df, path, most_frequent_movement_from_best_time)

    return images


def get_list_of_images(df, path, most_frequent_movements):
    images = []
    count = 0
    for mov in list(most_frequent_movements['movement']):
        images.append([mov])
        for img in list(df.loc[df['movement'] == mov]['id']):
            try:
                infile = os.path.join(path, img + IMG_EXTENSION)
                im = Image.open(infile)
                if im.format == 'JPEG' and im.mode == 'RGB':
                    images[count].append(img)
            except:
                pass
        count +=1

    images.sort(key=lambda x: len(x), reverse=True)
    images = images[:10]
    for i in images:
        logging.info('El movimiento ' + i[0] + ' tiene ' + str(len(i)-1) + ' imagenes validas')

    return images


def create_new_trainset(ntrain, nvalid, images, path):
    random.seed(datetime.now())

    movements = ['cubism', 'impressionism', 'symbolism', 'postpainterly_abstraction', 'postimpressionism']

    valid_images_per_movement = []

    for movement in movements:
        for i in images:
            if i[0] == movement:
                valid_images_per_movement.append(i)

    train = {
        'cubism': [],
        'impressionism': [],
        'postpainterly_abstraction': [],
        'symbolism': [],
        'postimpressionism': []
    }

    validate = {
        'cubism': [],
        'impressionism': [],
        'postpainterly_abstraction': [],
        'symbolism': [],
        'postimpressionism': []
    }

    for mov in valid_images_per_movement:

        for i in range(ntrain):
            painting = random.choice(mov[1:])
            mov.remove(painting)
            train[mov[0]].append(painting)
        for i in range(nvalid):
            painting = random.choice(mov[1:])
            mov.remove(painting)
            validate[mov[0]].append(painting)

    # os.mkdir(path='dataset/validate')
    dataset = os.path.join(os.getcwd(), PATH_DATASET)
    train_path = os.path.join(dataset, 'train')
    validate_path = os.path.join(dataset, 'validate')
    for mov in movements:
        try:
            shutil.rmtree(os.path.join(train_path, mov))
            shutil.rmtree(os.path.join(validate_path, mov))
            os.mkdir(path=os.path.join(train_path, mov))
            os.mkdir(path=os.path.join(validate_path, mov))
        except:
            pass
        for img in train[mov]:
            try:
                infile = os.path.join(path, img + IMG_EXTENSION)
                outfile = os.path.join(train_path, img + IMG_EXTENSION)
                im = Image.open(infile)
                (w, h) = im.size

                left = (w - 264) / 2
                top = (h - 264) / 2
                right = (w + 264) / 2
                bottom = (h + 264) / 2

                cropped = im.crop((left, top, right, bottom))
                cropped.save(outfile)
                # shutil.copyfile(infile, outfile)
            except Exception as ex:
                print(ex)
        for img in validate[mov]:
            try:
                infile = os.path.join(path, img + IMG_EXTENSION)
                outfile = os.path.join(validate_path, img + IMG_EXTENSION)
                im = Image.open(infile)
                (w, h) = im.size

                left = (w - 50) / 2
                top = (h - 50) / 2
                right = (w + 50) / 2
                bottom = (h + 50) / 2

                cropped = im.crop((left, top, right, bottom))
                cropped.save(outfile)
                # shutil.copyfile(infile, outfile)
            except Exception as ex:
                print(ex)
    return (train, validate)


def main(args):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    log_dir = os.path.join(os.getcwd(), LOGS_FOLDER_NAME)
    str_datetime = datetime.now().strftime('%S%M%H%d%m%Y')

    if not os.path.exists(log_dir):
        print('Creating logs directory in', log_dir)
        os.mkdir(log_dir)

    log_file = os.path.join(log_dir, str_datetime + '.log')
    logging.basicConfig(filename=log_file, filemode='w', level=logging.DEBUG, format=LOGS_FORMAT)
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(LOGS_FORMAT)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    images = []

    if valid_fetch(args):
        images = fetch(args.path, args.csv)
    if valid_new_trainset(args):
        create_new_trainset(args.train, args.validate, images, args.path)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Train a Neuronal Network.')

    parser.add_argument('--csv', type=str, help='path to the csv file', required=False)
    parser.add_argument('--path', type=str, help='path to the dataset', required=False)
    parser.add_argument('-f', '--fetch', help='print stadistics and create a valid set of data', action='store_true')
    parser.add_argument('--new-trainset', help='create a new set of training', action='store_true')
    parser.add_argument('--train', type=int, help='number of image for training', required=False)
    parser.add_argument('--validate', type=int, help='number of image for training', required=False)

    args = parser.parse_args()

    if not validate_args(args):
        parser.print_help()
    else:
        main(args)

