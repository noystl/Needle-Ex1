from selenium import webdriver
from scrapy.selector import Selector
import math
import json
import time


class Scraper:
    DEFAULT_PROJECT_AMOUNT = 36
    PROJECTS_PER_PAGE = 12
    WAITING_TIME = 2
    KIKSTARTER_URL = 'https://www.kickstarter.com/discover/categories/technology'
    CREATOR_XPATH = '//*[@class="type-14 bold"]/text()'
    TITLE_XPATH = '//*[@class="type-28 type-24-md soft-black mb1 project-name"]/text()'
    DOLLARS_PLEDGED_XPATH = '//*[@class="ksr-green-500"]/text()'
    DOLLARS_GOAL_XPATH = '//*[@class="money"]/text()'
    NUM_BACKERS_XPATH = '//*[@class="block type-16 type-28-md bold dark-grey-500"]/span/text()'
    DAYS_TO_GO_XPATH = '//*[@class="block type-16 type-28-md bold dark-grey-500"]/text()'
    ALL_OR_NOTHING_PART1_XPATH = '//*[@class="link-soft-black medium"]/a/text()'
    ALL_OR_NOTHING_PART2_XPATH = '//*[@class="mb3 mb0-lg type-12"]/span/text()'
    PROJECT_LINK_XPATH = '//*[@class="clamp-5 navy-500 mb3 hover-target"]'
    LOAD_MORE_BUTTON_XPATH = '//*[@class="bttn bttn-green bttn-medium"]'

    def __init__(self, amount_to_load=DEFAULT_PROJECT_AMOUNT):
        """
        :param amount_to_load:
        """
        self.__driver = webdriver.Chrome(executable_path=r'resources\chromedriver.exe')
        self.__driver.minimize_window()
        self.__amountToLoad = amount_to_load
        self.__links = set()

    def __load_all_projects_divs(self):
        """
        Clicks on the "load more" button until the page contains enough project divs.
        :return:
        """
        clicks_required = int(math.ceil(self.DEFAULT_PROJECT_AMOUNT / self.PROJECTS_PER_PAGE))
        for i in range(clicks_required):
            time.sleep(self.WAITING_TIME)
            self.__driver.find_element_by_xpath(self.LOAD_MORE_BUTTON_XPATH).click()

    def __generate_projects_links(self):
        """
        :return:
        """
        print("Collecting links...")
        self.__driver.get(self.KIKSTARTER_URL)
        self.__load_all_projects_divs()
        project_divs = self.__driver.find_elements_by_xpath(self.PROJECT_LINK_XPATH)

        for element in project_divs:
            inner_html = element.get_attribute('innerHTML')
            link = inner_html.split("\"")[1]
            self.__links.add(link)

        print("Finished collecting " + str(len(self.__links)) + " links.")

    def __parse_project_page(self, project_link, project_id):
        project_data = {}
        self.__driver.get(project_link)
        project_html = self.__driver.page_source
        project_data['id'] = project_id
        project_data['url'] = project_link
        project_data['Creator'] = Selector(text=project_html).xpath(self.CREATOR_XPATH).get()
        project_data['Title'] = Selector(text=project_html).xpath(self.TITLE_XPATH).get()
        # project_data['Text'] = project_html           todo: uncomment before final execution.
        project_data['DollarsPledged'] = Selector(text=project_html).xpath(self.DOLLARS_PLEDGED_XPATH).get()
        project_data['DollarsGoal'] = Selector(text=project_html).xpath(self.DOLLARS_GOAL_XPATH).get()
        project_data['NumBackers'] = Selector(text=project_html).xpath(self.NUM_BACKERS_XPATH).get()
        project_data['DaysToGo'] = Selector(text=project_html).xpath(self.DAYS_TO_GO_XPATH).get()
        project_data['AllOrNothing'] = Selector(text=project_html).xpath(self.ALL_OR_NOTHING_PART1_XPATH).get()
        project_data['AllOrNothing'] += " " + Selector(text=project_html).xpath(self.ALL_OR_NOTHING_PART2_XPATH).get()
        print("Created a dictionary for project " + str(project_id) + " out of " + str(self.DEFAULT_PROJECT_AMOUNT))
        return project_data

    def __create_projects_dictionary(self):
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
        print("Start scraping...")
        self.__generate_projects_links()
        data = self.__create_projects_dictionary()
        with open("results.json", 'w') as results_file:
            json.dump(data, results_file, indent=4)
        print("Finished scraping.")

    def __del__(self):
        """
        Closes the driver.
        :return:
        """
        self.__driver.close()


if __name__ == '__main__':
    scraper = Scraper()
    scraper.scrap()
