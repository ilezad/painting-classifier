#!/usr/bin/python3

from bs4 import BeautifulSoup
from requests import get
import re
import os
import csv
import logging


class Artist:
    def __init__(self, link, name):
        self.link = link
        self.name = name


class Movement:
    def __init__(self, name, link):
        self.name = name
        self.link = link


def main():
    try:
        html = get('https://www.wikiart.org/en/artists-by-art-movement')
        soup = BeautifulSoup(html.text, 'html.parser')

        list_rows = []
        outfile = open('dataset.csv', 'w')
        writer = csv.writer(outfile)

        logging.basicConfig(filename='web_scraper.log', level=logging.DEBUG)

        movement_list = []
        for li in soup.find_all('li', {'class': 'dottedItem'})[1:]:
            a = li.find('a')
            movement = '_'.join(li.a.text.lower().split(' ')[:-1])
            link = 'https://www.wikiart.org' + a.get('href') + '/text-list'
            movement_list.append(Movement(movement, link))

        for li in soup.find_all('li', {'class': 'header'})[:-7]:
            time = li.find('span').text
            logging.info(time.upper())
            print('[+] ' + time.upper())
            times[time](time, movement_list, list_rows)

        for li in soup.find_all('li', {'class': 'header'})[-6:]:
            time = li.find('span').text
            logging.info(time.upper())
            print('[+] ' + time.upper())
            times[time](time, movement_list, list_rows)

        # times['Contemporary Art'](time, movement_list, list_rows)

        writer.writerow(['id', 'time', 'movement', 'author', 'painting_name'])
    except Exception as ex:
        logging.critical(ex)
        logging.info('\n[!] Scrapping OFF')
        print('\n[!] Scrapping OFF')
    finally:
        writer.writerows(list_rows)


def ancient_greek_art(time, movement_list, list_rows):
    for movement in movement_list[0:2]:
        get_movement(time, movement.name, movement.link, list_rows)


def medieval_art(time, movement_list, list_rows):
    for movement in movement_list[2:6]:
        get_movement(time, movement.name, movement.link, list_rows)


def renaissance_art(time, movement_list, list_rows):
    for movement in movement_list[6:11]:
        get_movement(time, movement.name, movement.link, list_rows)


def post_renaissance_art(time, movement_list, list_rows):
    for movement in movement_list[11:17]:
        get_movement(time, movement.name, movement.link, list_rows)


def moder_art(time, movement_list, list_rows):
    for movement in movement_list[17:94]:
        get_movement(time, movement.name, movement.link, list_rows)


def contemporary_art(time, movement_list, list_rows):
    for movement in movement_list[94:124]:
        get_movement(time, movement.name, movement.link, list_rows)


def chinese_art(time, movement_list, list_rows):
    for movement in movement_list[124:135]:
        get_movement(time, movement.name, movement.link, list_rows)


def korean_art(time, movement_list, list_rows):
    for movement in movement_list[135:138]:
        get_movement(time, movement.name, movement.link, list_rows)


def japanese_art(time, movement_list, list_rows):
    for movement in movement_list[138:145]:
        get_movement(time, movement.name, movement.link, list_rows)


def islamic_art(time, movement_list, list_rows):
    for movement in movement_list[145:153]:
        get_movement(time, movement.name, movement.link, list_rows)


def native_art(time, movement_list, list_rows):
    get_movement(time, movement_list[153].name, movement_list[153].link, list_rows)


def ancient_egyptian_art(time, movement_list, list_rows):
    get_movement(time, movement_list[154].name, movement_list[154].link, list_rows)


times = {
    'Ancient Greek Art': ancient_greek_art,
    'Medieval Art': medieval_art,
    'Renaissance Art': renaissance_art,
    'Post Renaissance Art': post_renaissance_art,
    'Modern Art': moder_art,
    'Contemporary Art': contemporary_art,
    'Chinese Art': chinese_art,
    'Korean Art': korean_art,
    'Japanese Art': japanese_art,
    'Islamic Art': islamic_art,
    'Native Art': native_art,
    'Ancient Egyptian art': ancient_egyptian_art
}


def get_movement(time, movement, movement_link, list_rows):
    artists = get_artists(movement, movement_link)

    total = 0
    for artist in artists:
        cont = get_paintings(time, movement.replace('(', '').replace(')', '').replace('-', ''), artist, list_rows)
        logging.info(artist.name + ':' + str(cont))
        print('[' + str(cont) + ']\t' + artist.name)
        total += cont
    logging.info('TOTAL: ' + str(total))
    print('[+] TOTAL: ' + str(total))
    return total


def get_artists(movement, movement_link):
    artists = []
    try:
        html = get(movement_link)
        soup = BeautifulSoup(html.text, 'html.parser')

        for link in soup.find('div', {'class': 'masonry-text-view'}).find_all('a'):
            if re.search('a href', str(link)):
                artists.append(Artist('https://www.wikiart.org' + link.get('href') + '/all-works/text-list', link.text))
        logging.info('Numero de links de ' + movement.replace('_', ' ') + ': ' + str(len(artists)))
        print('[+] Numero de links de ' + movement.replace('_', ' ') + ': ' + str(len(artists)))
    except Exception as ex:
        logging.error(ex)
        pass
    finally:
        return artists


def get_paintings(time, movement, artist, list_rows):
    cont = 0
    try:
        html = get(artist.link)
        soup = BeautifulSoup(html.text, 'html.parser')
        for li in soup.find('ul', {'class': 'painting-list-text'}).find_all('a'):
            name = artist.name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '')
            link = 'https://www.wikiart.org' + li.get('href')
            if os.path.isfile('dataset/' + movement + '/' + name + '__' + str(cont) + '.jpg') or download_painting(
                    movement, artist.name, link, cont):
                list_rows.append(
                    [movement + '/' + name + '__' + str(cont), time, movement.replace('_', ' '), artist.name, li.text])
                logging.debug('dataset/' + movement + '/' + name + '__' + str(cont) + '.jpg')
                cont += 1
            if cont == 200:
                break
    except Exception as ex:
        logging.error(ex)
        pass
    finally:
        return cont


def download_painting(movement, artist_name, painting_link, cont):
    html = get(painting_link)
    soup = BeautifulSoup(html.text, 'html.parser')
    link = soup.find('img').get('src')
    try:
        if not os.path.exists('dataset/' + movement):
            os.makedirs('dataset/' + movement)
        name = artist_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '')
        with open('dataset/' + movement + '/' + name + '__' + str(cont) + '.jpg', 'wb') as file:
            file.write(get(link).content)
    except Exception as ex:
        logging.error(ex)
        return False
    return True


if __name__ == "__main__":
    main()
