
#Imports:
from selenium import webdriver
from scrapy.selector import Selector
import math
import json
import time


class Scraper:
    DEFAULT_PROJECT_AMOUNT = 300
    PROJECTS_PER_PAGE = 12
    WAITING_TIME = 2
    HOURS_IN_DAY = 24.0
    KICKSTARTER_URL = 'https://www.kickstarter.com/discover/categories/technology'
    CREATOR_XPATH = '//*[@class="type-14 bold"]/text()'
    TITLE_XPATH = '//*[@class="type-28 type-24-md soft-black mb1 project-name"]/text()'
    DOLLARS_PLEDGED_XPATH = '//*[@class="ksr-green-500"]/text()'
    DOLLARS_GOAL_XPATH = '//*[@class="money"]/text()'
    NUM_BACKERS_XPATH = '//*[@class="block type-16 type-28-md bold dark-grey-500"]/span/text()'
    TIME_LEFT_XPATH = '//*[@class="block type-16 type-28-md bold dark-grey-500"]/text()'
    TIME_TYPE_XPATH = '//*[@class="block navy-600 type-12 type-14-md lh3-lg"]/text()'
    PROJECT_LINK_XPATH = '//*[@class="clamp-5 navy-500 mb3 hover-target"]'
    LOAD_MORE_BUTTON_XPATH = '//*[@class="bttn bttn-green bttn-medium"]'

    def __init__(self, amount_to_load=DEFAULT_PROJECT_AMOUNT):
        """
        Initializes a scraper object.
        :param amount_to_load: the number project divs to crawl.
        """
        self.__driver = webdriver.Chrome(executable_path=r'resources\chromedriver.exe')
        self.__driver.minimize_window()
        self.__amountToLoad = amount_to_load
        self.__links = set()

    def __load_all_projects_divs(self):
        """
        Clicks on the "load more" button until the page contains enough projects.
        """
        clicks_required = int(math.ceil(self.DEFAULT_PROJECT_AMOUNT / self.PROJECTS_PER_PAGE))
        for i in range(clicks_required):
            time.sleep(self.WAITING_TIME)
            self.__driver.find_element_by_xpath(self.LOAD_MORE_BUTTON_XPATH).click()

    def __generate_projects_links(self):
        """
        Generates the set of project links.
        """
        print("Collecting links...")
        self.__driver.get(self.KICKSTARTER_URL)
        self.__load_all_projects_divs()
        project_divs = self.__driver.find_elements_by_xpath(self.PROJECT_LINK_XPATH)

        for element in project_divs:
            inner_html = element.get_attribute('innerHTML')
            link = inner_html.split("\"")[1]  # To handle cases in which escaping is evident
            self.__links.add(link)

        print("Finished collecting " + str(len(self.__links)) + " links.")

    def __extract_days_to_go(self, html):
        """
        Computes the days left to the project. More specifically, If the the project displays
        it's time by hours, it will converts it to days.
        :param html: the projects text (html).
        :return: the time left foe the project to close, in days.
        """
        time_type = Selector(text=html).xpath(self.TIME_TYPE_XPATH).get()
        time_left = Selector(text=html).xpath(self.TIME_LEFT_XPATH).get()
        if time_type.startswith('hours'):
            return str(float(time_left) / self.HOURS_IN_DAY)
        return time_left

    # def __remove_delimiter(self, scrap_result):
    #     if 'Delimiter' in scrap_result:
    #

    def __parse_project_page(self, project_link, project_id):
        """
        Collects all of the project page relevant data: Creator, Title, Text , DollarsPledged, DollarsGoal,
        NumBackers, DaysToGo.
        :param project_link: the project's link.
        :param project_id: the projects id- non zero int.
        :return: returns a set containing the page's data.
        """
        project_data = {}
        self.__driver.get(project_link)
        time.sleep(self.WAITING_TIME)
        project_html = self.__driver.page_source
        project_data['id'] = project_id
        project_data['url'] = project_link
        project_data['Creator'] = Selector(text=project_html).xpath(self.CREATOR_XPATH).get()
        project_data['Title'] = Selector(text=project_html).xpath(self.TITLE_XPATH).get()
        project_data['Text'] = project_html
        project_data['DollarsPledged'] = Selector(text=project_html).xpath(self.DOLLARS_PLEDGED_XPATH).get().replace('Delimiter', ',')
        project_data['DollarsGoal'] = Selector(text=project_html).xpath(self.DOLLARS_GOAL_XPATH).get().replace('Delimiter', ',')
        project_data['NumBackers'] = Selector(text=project_html).xpath(self.NUM_BACKERS_XPATH).get().replace('Delimiter', ',')
        project_data['DaysToGo'] = self.__extract_days_to_go(project_html).replace('Delimiter', ',')
        print("Created a dictionary for project " + str(project_id) + " out of " + str(self.DEFAULT_PROJECT_AMOUNT))
        return project_data

    def __create_projects_dictionary(self):
        """
        Creates a dictionary of all project pages and their attributes.
        :return: returns the dictionary.
        """
        print("creating projects dictionary...")
        data = {'projects': []}
        project_num = 1
        for project_link in self.__links:
            time.sleep(self.WAITING_TIME)
            data['projects'].append(self.__parse_project_page(project_link, project_num))
            project_num += 1
        print("finished project dictionary creation.")
        return data

    def scrap(self):
        """
        Crawls the Kickstarter's site and outputs the data of the projects that are displayed
        there as a JSON file.
        """
        print("Start scraping...")
        self.__generate_projects_links()
        data = self.__create_projects_dictionary()
        with open("results.json", 'w', encoding='utf8') as results_file:
            json.dump(data, results_file, ensure_ascii=False, indent=4)
        print("Finished scraping.")

    def __del__(self):
        """
        Closes the driver.
        """
        self.__driver.close()


if __name__ == '__main__':
    scraper = Scraper()
    scraper.scrap()
