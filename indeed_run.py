'''
Module to run scraper module using list of keywords and locations list to search and
collect jobs details data in a csv file.

Date: 08-01-2024
Written by: Swati Mishra
'''

# imports
import pandas as pd
import os

from indeed_main import IndeedScraper

# main function to create instance of class IndeedScraper and call methods to collect data from all pages of the searched category
def main():
    scraper = IndeedScraper(['Python Analyst'], ['New Delhi, Delhi'])
    main_soup_list = scraper.get_main_soup_list()

    # loop through all searched category's soup objects
    for main_soup in main_soup_list:

        all_jobs_data, all_pages_urls = scraper.get_main_job_page_data(main_soup=main_soup)
        next_pages_soup_list = scraper.get_next_job_pages_soups(page_urls=all_pages_urls)
        df_jobs = scraper.get_next_pages_data_added(next_pages_soup_list=next_pages_soup_list, all_jobs_data=all_jobs_data)
        job_soups = scraper.collect_job_soups(df_jobs=df_jobs)
        df_jobs_full = scraper.add_job_descs_to_data_df(soup_list1=job_soups, df_jobs=df_jobs)

        # saving dataframe and updating the csv file
        if os.path.exists('indeed_scraped_data.csv'):
            df = pd.read_csv('indeed_scraped_data.csv')
            df_new = pd.concat([df_jobs_full, df])
            df_new.to_csv('indeed_scraped_data.csv', index=False)
        else:
            df_jobs_full.to_csv('indeed_scraped_data.csv', index=False)

# main function call
if __name__ == "__main__":
    main()
