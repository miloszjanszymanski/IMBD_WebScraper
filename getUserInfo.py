import bs4
import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import openpyxl
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

url = input("Provide the IMDB user page, example https://www.imdb.com/user/ur6387867: ")
url = url + "/ratings"
print(url)
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
page = driver.get(url)
xpath_selector = "//button[@data-testid='accept-button']"
click_accept_button = driver.find_element(By.XPATH, xpath_selector).click()
fullHeader = driver.find_element(By.XPATH, "//h1[contains(@class, 'header')]").text
userName = fullHeader.find("'")

if userName != -1:
    fullHeader = fullHeader[:userName]


def nextButtonIsVisible():
    buttons = driver.find_elements(By.CLASS_NAME, 'lister-page-next')
    return len(buttons) > 0


def clickNextPage():
    print("Click NEXT button")
    driver.find_element(By.CLASS_NAME, 'lister-page-next').click()


def isActorLink(linkTag: bs4.Tag):
    href = linkTag["href"]
    return href is not None and href.startswith("/name/")


def hasDirectorLink(movie: bs4.Tag):
    return "Director" in movie.text


def getActors(movie: bs4.Tag):
    allLinks = movie.find_all("a")
    actorLinks = list(filter(lambda linkTag: isActorLink(linkTag), allLinks))

    actorNames = [actor.text for actor in actorLinks]
    if hasDirectorLink(movie):
        return actorNames[1:]
    else:
        return actorNames


movie_names = []
movie_actors = []
movie_years = []
user_rank = []
imdb_rank = []
movie_genre = []

i = 1
while True:
    time.sleep(2)
    movies = soup.find_all("div", class_="lister-item-content")

    for i, movie in enumerate(movies, 1):
        rating = movie.find('span', class_="ipl-rating-star__rating")
        if not rating:
            continue
        if movie.find('span', class_="genre") is None:
            continue
        name = movie.find("a").text
        year = movie.find("span", class_="lister-item-year").text.strip("()")

        empty = ""
        for char in year:
            if char.isdigit():
                remaining_year = year[len(empty):]
                break
            empty += char
        actors = getActors(movie)
        print(actors)

        imdbrank = rating.get_text().strip()

        userRank = movie.find('div', class_="ipl-rating-star ipl-rating-star--other-user small").get_text().strip()
        genre = movie.find('span', class_="genre").get_text().strip()

        movie_names.append(name)
        movie_years.append(remaining_year)
        user_rank.append(userRank)
        imdb_rank.append(imdbrank)
        movie_genre.append(genre)
        movie_actors.append(", ".join(actors))

        i += 1
    if not nextButtonIsVisible():
        break

    clickNextPage()
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

data = {"Name": movie_names, "Genre": movie_genre, "Year": movie_years, "User rank": user_rank,
        "IMDB rank": imdb_rank, "Actors": movie_actors}
df = pd.DataFrame(data)
df.index += 1
df.to_excel(fullHeader + "_rating.xlsx", index=True)

workbook = openpyxl.load_workbook(fullHeader + "_rating.xlsx")
worksheet = workbook.active

for cell in worksheet['F2:F' + str(worksheet.max_row)]:
    if len(cell[0].value) == 1:
        continue

    cell[0].value = cell[0].value[0] + ',' + cell[0].value[2:]

workbook.save(fullHeader + "_rating.xlsx")

