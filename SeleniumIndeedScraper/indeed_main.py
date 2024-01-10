'''
Module to scrape jobs data from https://in.indeed.com with keywords and locations provided as input.

Date: 08-01-2024
Written by: Swati Mishra
'''

# imports
import json
import pandas as pd
import re
import time

from urllib.parse import urlencode
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# class scraper
class IndeedScraper:

    def __init__(self, keyword_list, location_list):
        """customizing selenium webdriver and declaring job keywords list and location list

        Args:
            keyword_list (_list_): job search keywords
            location_list (_list_): job search locations
        """        
        self.keyword_list = keyword_list
        self.location_list = location_list

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-notifications")

        self.driver = webdriver.Chrome(options=chrome_options)

    def get_indeed_search_url(self, keyword, location, offset=0): # pagination=0
        """Function to create and return a fully encoded indeed job page url based on
        job search keyword, location and pagination offset for each page for the same search category.
        Args:
            keyword (_type_): _job search keyword_
            location (_type_): _job search location_
            offset (int, optional): _pagination offset for each page for the same category_. Defaults to 0.

        Returns:
            _string_: _an indeed job page url for a job keyword and a location with a page offset for the category_
        """        
        if offset == 0:
            parameters = {"q": keyword, "l": location}
        else:
            parameters = {"q": keyword, "l": location, "start": offset}
        return "https://in.indeed.com/jobs?" + urlencode(parameters)

    def collect_urls(self):
        """_Function to collect indeed job page url based on job search keywords, locations and pagination offset=0
        to get main page urls for all categories.

        Returns:
            _list_: _list of main page urls for all keywords and locations provided_
        """        
        # keyword_list = ['Python Analyst']
        # location_list = ['New Delhi, Delhi']

        url_list = []
        for keyword in self.keyword_list:
            for location in self.location_list:
                indeed_jobs_url = self.get_indeed_search_url(keyword, location)
                # print(indeed_jobs_url)
                url_list.append(indeed_jobs_url)
        # url_list[0]
        return url_list

    def get_main_soup_list(self):
        """_Function to collect a list of BeautifulSoup soup objects for all category main page urls
        collected from method collect_urls.
        Returns:
            _list_: _list of BeautifulSoup soup objects_
        """        
        url_list = self.collect_urls(self.keyword_list, self.location_list)
        main_soup_list = []
        for url in url_list:
            self.driver.get(url)
            soupy = BeautifulSoup(self.driver.page_source, "html.parser")
            main_soup_list.append(soupy)
        self.driver.quit()

        return main_soup_list

    def get_main_job_page_data(self, soupy):
        """_Function to collect required jobs related data of all the jobs present in the BeautifulSoup soup object of the
        main page of a category. It also contains all jobs detail page urls created from the job_keys_

        Args:
            soupy (_BeautifulSoup object_): _BeautifulSoup soup object of main page of a category_

        Returns:
            _list_: _jobs data list_
            _list_: _urls of all next pages of the main page_
        """        
        script_tag_text = soupy.find("script", attrs={"id":"mosaic-data"}).getText(strip=True)
        script_job_text_data = re.findall('window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', script_tag_text)
        json_blob = json.loads(script_job_text_data[0])
        jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel']['results']
        print(len(jobs_list))

        all_jobs_data = []
        for each_job in jobs_list: # https://in.indeed.com/viewjob?cmp=MNR-Solutions&t=Data+Scientist&jk=
            jobs_data = []
            # print('\n', jobs_list.index(each_job))
            jobs_data.append(each_job['company'])
            jobs_data.append(each_job['companyRating'])
            jobs_data.append(each_job['displayTitle'])
            jobs_data.append(each_job['employerResponsive'])

            # convert all salary format as integer numbers to yearly
            try:
                sal_attr = each_job['extractedSalary']
                max_sal = sal_attr['max']
                min_sal = sal_attr['min']
                sal_type = sal_attr['type']

                if sal_type == 'monthly':
                    max_sal = max_sal * 12
                    min_sal = min_sal * 12
                
                # print((max_sal).bit_count()) # perfectly works
                if (max_sal).bit_count() < 4:
                    max_sal = 0
                if (min_sal).bit_count() < 4:
                    min_sal = 0

                jobs_data.append(max_sal)
                jobs_data.append(min_sal)
                jobs_data.append(sal_type)
            except:
                jobs_data.append(0)
                jobs_data.append(0)
                jobs_data.append('')
            jobs_data.append(each_job['formattedLocation'])
            jobs_data.append(each_job.get('formattedActivityDate', ''))
            jobs_data.append(each_job['formattedRelativeTime'])
            try:
                jobs_data.append(each_job['hiringMultipleCandidatesModel']['hiresNeededExact'])
            except:
                jobs_data.append('')
            # salary range snippet as text
            jobs_data.append(each_job['salarySnippet'].get('text', ''))
            # loop through attributes likes shifts, remote or not, benefits, type etc. as labels
            for attribute in each_job['taxonomyAttributes']:
                if attribute['attributes'] == []:
                    jobs_data.append('')
                else:
                    jobs_data.append(attribute['attributes'][0]['label'])
            jobs_data.append(each_job['urgentlyHiring'])

            # print(job.get('jobkey'))
            if each_job.get('jobkey') is not None:
                job_url = 'https://in.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk=' + each_job.get('jobkey')
                # print(job_url)
                # jobs_urls.append(job_url)
                jobs_data.append(job_url)
                # print(len(jobs_data))
            all_jobs_data.append(jobs_data)

        # all_jobs_data
        # jobs_urls # len= 15
        # len(all_jobs_data) # 15
        print(all_jobs_data[10]) # perfect

        # collect page numbers
        pagination_tags = soupy.find_all("li", class_="css-227srf eu4oa1w0")
        pages = [tag.getText(strip=True) for tag in pagination_tags if tag.getText(strip=True) != '']

        # loop through page numbers to add offset for each page which is 0 for first and increment to 10 for each
        offset = 10
        page_urls = []
        for num in pages[1:]:
            page_url = self.get_indeed_search_url(keyword='Python Analyst', location='New Delhi, Delhi', offset=offset)
            page_urls.append(page_url)
            offset = offset + 10
        return all_jobs_data, page_urls

    def get_next_job_pages_soups(self, page_urls):
        """_Function to get all the next pages as BeautifulSoup soup objects of category's main page using
        the list of all next page urls_

        Args:
            page_urls (_list_): _the list of all next page urls_

        Returns:
            _list_: _list of all next pages as BeautifulSoup soup objects_
        """        
        soup_list = []
        # loop through page urls and collect soups
        for link in page_urls:
            self.driver.get(link)
            time.sleep(2)
            soupy1 = BeautifulSoup(self.driver.page_source, "html.parser")
            soup_list.append(soupy1)
        self.driver.quit()

        return soup_list

    def get_next_pages_data_added(self, soup_list, all_jobs_data):
        """_Function to add each next page's jobs data to the main category page's collected data
        and return a complete dataframe of all the jobs data of the main page and the next pages._

        Args:
            soup_list (_list_): _BeautifulSoup objects list of all next pages of a main category page_
            all_jobs_data (_list_): _jobs data on all the jobs as advertised on the searched category's main page_

        Returns:
            _dataframe_: _a complete dataframe of all the jobs data of the main page and the next pages_
        """        
        all_jobs_data1 = []
        # loop through soups
        for soup_obj in soup_list:
            script_text = soup_obj.find("script", attrs={"id":"mosaic-data"}).getText(strip=True)
            script_job_data = re.findall('window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', script_text)
            json_blob_data = json.loads(script_job_data[0])
            # print(json_blob_data) # working

            jobs_list1 = json_blob_data['metaData']['mosaicProviderJobCardsModel']['results']
            # print(jobs_page_list) # working

            # loop through job list in a page's soup
            for each_job in jobs_list1: # https://in.indeed.com/viewjob?cmp=MNR-Solutions&t=Data+Scientist&jk=
                jobs_data1 = []
                # print('\n', jobs_list.index(each_job)) 
                jobs_data1.append(each_job['company'])
                jobs_data1.append(each_job['companyRating'])
                jobs_data1.append(each_job['displayTitle'])
                jobs_data1.append(each_job['employerResponsive'])

                # formatting all pay to yearly format
                try:
                    sal_attr = each_job['extractedSalary']
                    max_sal = sal_attr['max']
                    min_sal = sal_attr['min']
                    sal_type = sal_attr['type']

                    if sal_type == 'monthly':
                        max_sal = max_sal * 12
                        min_sal = min_sal * 12

                    # print((max_sal).bit_count()) # perfectly works
                    if (max_sal).bit_count() < 4:
                        max_sal = 0
                    if (min_sal).bit_count() < 4:
                        min_sal = 0

                    jobs_data1.append(max_sal)
                    jobs_data1.append(min_sal)
                    jobs_data1.append(sal_type)
                except:
                    jobs_data1.append(0)
                    jobs_data1.append(0)
                    jobs_data1.append('')
                jobs_data1.append(each_job['formattedLocation'])
                jobs_data1.append(each_job.get('formattedActivityDate', ''))
                jobs_data1.append(each_job['formattedRelativeTime'])
                try:
                    jobs_data1.append(each_job['hiringMultipleCandidatesModel']['hiresNeededExact'])
                except:
                    jobs_data1.append('')
                jobs_data1.append(each_job['salarySnippet'].get('text', ''))

                # loop through attributes likes shifts, remote or not, benefits, type etc. as labels
                for attribute in each_job['taxonomyAttributes']:
                    if attribute['attributes'] == []:
                        jobs_data1.append('')
                    else:
                        jobs_data1.append(attribute['attributes'][0]['label'])
                jobs_data1.append(each_job['urgentlyHiring'])

                # print(job.get('jobkey'))
                if each_job.get('jobkey') is not None:
                    job_url1 = 'https://in.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk=' + each_job.get('jobkey')
                    # print(job_url1)
                    jobs_data1.append(job_url1)
                # print(len(jobs_data1)) # 20
                all_jobs_data1.append(jobs_data1)

        # extending data for the page 1 to the data collected for the rest of the pages
        all_jobs_data1.extend(all_jobs_data)
        print(len(all_jobs_data1)) # 75
        print(all_jobs_data1[70])

        columns = ['company', 'companyRating', 'displayTitle', 'employerResponsive', 'max_salary', 'min_salary', 'type', 'formattedLocation',
            'formattedActivityDate', 'formattedRelativeTime', 'hiresNeededExact', 'salarySnippet', 'job_type', 'shift', 'remote',
            'benefits', 'job_type_cc', 'schedules', 'urgentlyHiring', 'job_url']
        print(len(columns))
        df_jobs = pd.DataFrame(all_jobs_data1, columns=columns) # perfect
        return df_jobs

    def collect_job_soups(self, df_jobs):
        """_Function to collect BeautifulSoup objects of each job detail page from the dataframe of the job category's all pages data_

        Args:
            df_jobs (_dataframe_): _dataframe of the job category's all pages data_

        Returns:
            _list_: _list of BeautifulSoup objects of each job detail page collected from all category pages_
        """        
        jobs_urls_list = df_jobs["job_url"]
        soup_list1 = []

        # loop through soups
        for job_link in jobs_urls_list:
            self.driver.get(job_link)
            time.sleep(2)
            # close the pop notification
            try:
                WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button.popover-x-button-close.icl-CloseButton"))).click()
            except:
                pass
            soupy2 = BeautifulSoup(self.driver.page_source, "html.parser")
            soup_list1.append(soupy2)
        self.driver.quit()

        print(len(soup_list1)) # 75
        return soup_list1

    def add_job_descs_to_data_df(self, soup_list1, df_jobs):
        """_Function to collect job descriptions from all jobs detail page soups and add to the jobs dataframe_

        Args:
            soup_list1 (_list_): _list of BeautifulSoup objects of each job detail page_
            df_jobs (_dataframe_): _dataframe of the job category's all pages data_

        Returns:
            _dataframe_: _complete dataframe with job descriptions added to the dataframe_
        """        
        job_page_list1 = []
        # loop through soups
        for page_soup in soup_list1:

            job_data_list = []

            job_desc = page_soup.find("div", attrs={"id":"jobDescriptionText"})
            # print(type(job_desc)) # working
            # print(job_desc)
            list1 = job_desc.find_all("li")
            list1_desc = [tag.getText(strip=True) for tag in list1]
            job_data_list.append(list1_desc)

            list2 = job_desc.find_all("p")
            list2_desc = [tag.getText(strip=True) for tag in list2]
            job_data_list.append(list2_desc)
            job_page_list1.append(job_data_list)

        # adding descriptions dataframe to the main data dataframe
        print(len(job_page_list1)) # 75
        columns2 = ['job_desc1', 'job_desc2']
        df_desc = pd.DataFrame(job_page_list1, columns=columns2)
        df_jobs_full = pd.concat([df_jobs, df_desc], axis=1) # perfect

        return df_jobs_full
